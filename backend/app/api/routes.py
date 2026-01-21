# D:\Year 5\S1\Advanced_programming\article_classifier\backend\app\api\routes.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import logging
import traceback

from app.db.session import get_db
from app.db import crud
from app.ml.model import classifier
from app.db.schemas import PredictionResponse
from app.ml import preprocessing

router = APIRouter(tags=['api'])
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────
# Schemas
# ────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    feedback: bool


class SegmentRequest(BaseModel):
    text_input: str
    max_words: int = 512


class PaginatedResponse(BaseModel):
    predictions: List[PredictionResponse]
    total: int
    page: int
    limit: int
    total_pages: int


class TextValidationRequest(BaseModel):
    text_input: str
    min_words: Optional[int] = 50
    min_chars: Optional[int] = 100
    min_khmer_percentage: Optional[float] = 50.0


class TextValidationResponse(BaseModel):
    valid: bool
    message: str
    validation_info: Dict[str, Any]
    suggestions: Optional[List[str]] = None


# ────────────────────────────────────────────────
# Khmer segmentation endpoint
# ────────────────────────────────────────────────

@router.post("/segment")
def segment_text(payload: SegmentRequest):
    """
    Endpoint: POST /segment
    Returns Khmer word count, list of words (up to max_words), truncated flag, etc.
    Uses khmernltk for proper Khmer tokenization.
    """
    try:
        logger.info("📥 Segment request received")
        logger.info(f"   Text length: {len(payload.text_input)} characters")
        logger.info(f"   Max words: {payload.max_words}")
        logger.info(f"   Text preview: {payload.text_input[:50]!r}...")
        logger.debug(f"   First 10 char codes: {[f'U+{ord(c):04X}' for c in payload.text_input[:10]]}")

        # Clean text
        cleaned = preprocessing.remove_non_khmer_english_and_punct(payload.text_input)
        logger.info(f"✨ Text cleaned: {len(cleaned)} characters")

        if not cleaned:
            logger.warning("⚠️ Cleaned text is empty!")
            return {
                "khmer_word_count": 0,
                "khmer_words": [],
                "truncated": False,
                "cleaned_text": "",
                "warning": "Text became empty after cleaning"
            }

        # Segment using khmernltk
        result = preprocessing.count_khmer_words(cleaned, max_words=payload.max_words)

        logger.info(f"📊 Segmentation complete → count: {result['count']}, truncated: {result['truncated']}")
        logger.debug(f"   First 5 words: {result['words'][:5] if result['words'] else 'none'}")

        return {
            "khmer_word_count": result["count"],
            "khmer_words": result["words"],
            "truncated": result["truncated"],
            "cleaned_text": cleaned,
        }

    except Exception as e:
        logger.error(f"❌ Error in /segment: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────────────────────────────────────
# Debug endpoint for Khmer processing
# ────────────────────────────────────────────────

@router.post("/debug/khmer")
def debug_khmer_text(payload: SegmentRequest):
    """
    Debug endpoint — helps diagnose Khmer segmentation & khmernltk issues
    """
    try:
        text = payload.text_input
        debug_info = {
            "input_text": text,
            "input_length": len(text),
            "input_preview": text[:80] if len(text) > 80 else text,
        }

        cleaned = preprocessing.remove_non_khmer_english_and_punct(text)
        debug_info["cleaned_text"] = cleaned
        debug_info["cleaned_length"] = len(cleaned)

        # Try khmernltk
        try:
            from khmernltk import word_tokenize
            words = word_tokenize(cleaned)
            debug_info.update({
                "khmernltk_installed": True,
                "khmernltk_word_count": len(words),
                "khmernltk_words_preview": words[:10],
            })
        except ImportError as e:
            debug_info["khmernltk_installed"] = False
            debug_info["khmernltk_error"] = str(e)
        except Exception as e:
            debug_info["khmernltk_error"] = str(e)

        # Fallback split
        space_words = cleaned.split()
        debug_info["space_split_count"] = len(space_words)
        debug_info["space_split_words_preview"] = space_words[:8]

        # Actual function result
        result = preprocessing.count_khmer_words(cleaned, max_words=payload.max_words)
        debug_info["count_khmer_words_result"] = {
            "count": result["count"],
            "words_preview": result["words"][:6] if result["words"] else [],
            "truncated": result["truncated"]
        }

        return debug_info

    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


# ────────────────────────────────────────────────
# Text validation endpoint
# ────────────────────────────────────────────────

@router.post("/validate-text", response_model=TextValidationResponse)
def validate_text(payload: TextValidationRequest):
    """Validate if text is suitable for classification"""
    try:
        logger.info("🔍 Text validation request received")
        logger.info(f"   Text length: {len(payload.text_input)} characters")
        logger.info(f"   Requirements: min_words={payload.min_words}, min_chars={payload.min_chars}, min_khmer={payload.min_khmer_percentage}%")
        
        # Use the new validation method from model.py
        validation_result = classifier.predict_with_validation(
            payload.text_input,
            min_khmer_percentage=payload.min_khmer_percentage,
            min_words=payload.min_words,
            min_chars=payload.min_chars
        )
        
        if validation_result["valid"]:
            logger.info(f"✅ Text validation passed: {validation_result.get('validation_info', {})}")
        else:
            logger.warning(f"⚠️ Text validation failed: {validation_result.get('error', 'Unknown error')}")
        
        # Convert to TextValidationResponse format
        return TextValidationResponse(
            valid=validation_result["valid"],
            message=validation_result.get("error", "Text validation passed") if not validation_result["valid"] else "Text is valid for classification",
            validation_info=validation_result.get("validation_info", {}),
            suggestions=validation_result.get("suggestions")
        )
        
    except Exception as e:
        logger.error(f"❌ Validation error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────────────────────────────────────
# Text analysis endpoint
# ────────────────────────────────────────────────

@router.post("/analyze-text")
def analyze_text(payload: SegmentRequest):
    """Analyze text characteristics without prediction"""
    try:
        logger.info("📊 Text analysis request received")
        logger.info(f"   Text length: {len(payload.text_input)} characters")
        
        analysis_result = classifier.analyze_text(payload.text_input)
        
        logger.info(f"📈 Analysis complete: {analysis_result.get('khmer_percentage', 0):.1f}% Khmer")
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"❌ Analysis error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────────────────────────────────────
# Main prediction endpoint
# ────────────────────────────────────────────────

@router.post("/predict", response_model=PredictionResponse)
def predict_article(
    text_input: str = Body(..., embed=True),
    feedback: Optional[bool] = Body(None),
    min_words: Optional[int] = Body(50, description="Minimum words required"),
    min_chars: Optional[int] = Body(100, description="Minimum characters required"),
    min_khmer_percentage: Optional[float] = Body(50.0, description="Minimum Khmer percentage required"),
    db: Session = Depends(get_db)
):
    """Classify Khmer article text with validation"""
    try:
        logger.info("🎯 Prediction request received")
        logger.info(f"   Text length: {len(text_input)} characters")
        logger.info(f"   Validation requirements: min_words={min_words}, min_chars={min_chars}, min_khmer={min_khmer_percentage}%")
        
        # First validate the text
        validation_result = classifier.predict_with_validation(
            text_input,
            min_khmer_percentage=min_khmer_percentage,
            min_words=min_words,
            min_chars=min_chars
        )
        
        if not validation_result["valid"]:
            # Text validation failed
            error_msg = validation_result.get("error", "Text validation failed")
            validation_info = validation_result.get("validation_info", {})
            
            logger.warning(f"❌ Prediction rejected: {error_msg}")
            
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": error_msg,
                    "validation_info": validation_info,
                    "suggestion": f"Please provide longer Khmer text (minimum {min_words} words or {min_chars} characters with {min_khmer_percentage}% Khmer content)"
                }
            )
        
        # If validation passed, proceed with prediction
        processed_text = preprocessing.preprocess_for_model(text_input)
        
        # Get prediction
        category, confidence, prediction_info = classifier.predict(
            processed_text,
            min_khmer_percentage=min_khmer_percentage,
            min_words=min_words,
            min_chars=min_chars,
            skip_validation=True  # Already validated
        )
        
        # Log successful prediction
        logger.info(f"✅ Prediction successful: {category} ({confidence:.3f}%)")
        
        # Save to database
        db_prediction = crud.create_prediction(
            db=db,
            text_input=text_input,           # original text
            label_classified=category,
            accuracy=confidence,
            feedback=feedback
        )
        
        # Convert SQLAlchemy object to dict and add validation info
        response_dict = {k: v for k, v in db_prediction.__dict__.items() if not k.startswith('_')}
        response_dict["validation_info"] = validation_result.get("validation_info", {})
        
        # Ensure the response matches PredictionResponse schema
        return response_dict

    except HTTPException as http_error:
        # Re-raise HTTP exceptions
        raise http_error
    except Exception as e:
        logger.error(f"❌ Prediction error: {e}")
        logger.error(traceback.format_exc())
        crud.create_error_log(
            db=db,
            error_message=str(e),
            error_type="MODEL",
            endpoint="/predict"
        )
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────────────────────────────────────
# Get probabilities endpoint
# ────────────────────────────────────────────────

@router.post("/probabilities")
def get_probabilities(
    text_input: str = Body(..., embed=True),
    min_words: Optional[int] = Body(50, description="Minimum words required"),
    min_chars: Optional[int] = Body(100, description="Minimum characters required"),
    min_khmer_percentage: Optional[float] = Body(50.0, description="Minimum Khmer percentage required")
):
    """Get probabilities for all categories with validation"""
    try:
        logger.info("📊 Probabilities request received")
        logger.info(f"   Text length: {len(text_input)} characters")
        
        # First validate the text
        validation_result = classifier.predict_with_validation(
            text_input,
            min_khmer_percentage=min_khmer_percentage,
            min_words=min_words,
            min_chars=min_chars
        )
        
        if not validation_result["valid"]:
            # Validation failed
            error_msg = validation_result.get("error", "Text validation failed")
            validation_info = validation_result.get("validation_info", {})
            
            logger.warning(f"❌ Probabilities request rejected: {error_msg}")
            
            raise HTTPException(
                status_code=400,
                detail={
                    "error": error_msg,
                    "validation_info": validation_info,
                    "suggestion": f"Please provide longer Khmer text (minimum {min_words} words or {min_chars} characters with {min_khmer_percentage}% Khmer content)"
                }
            )
        
        # If valid, get probabilities
        processed_text = preprocessing.preprocess_for_model(text_input)
        
        # Use the get_all_probabilities method
        probabilities_result = classifier.get_all_probabilities(
            processed_text,
            min_khmer_percentage=min_khmer_percentage,
            min_words=min_words,
            min_chars=min_chars
        )
        
        if not probabilities_result.get("valid", True):
            # This shouldn't happen since we already validated
            raise HTTPException(status_code=500, detail="Unexpected validation failure")
        
        logger.info(f"✅ Probabilities calculated successfully")
        return probabilities_result
        
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        logger.error(f"❌ Probabilities error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────────────────────────────────────
# History & feedback
# ────────────────────────────────────────────────

@router.get("/predictions", response_model=PaginatedResponse)
def get_predictions(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get predictions with pagination"""
    try:
        logger.info(f"📜 History request - page: {page}, limit: {limit}")
        
        # Validate inputs
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 10
        
        # Calculate skip
        skip = (page - 1) * limit
        
        # Get total count
        total = crud.get_total_predictions(db)
        logger.info(f"📊 Total predictions in database: {total}")
        
        # Get paginated predictions (most recent first)
        predictions = crud.get_predictions_with_pagination(db, skip=skip, limit=limit)
        logger.info(f"📋 Retrieved {len(predictions)} predictions for page {page}")
        
        # Calculate total pages
        total_pages = (total + limit - 1) // limit if limit > 0 else 0
        
        return PaginatedResponse(
            predictions=predictions,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(f"❌ Error getting predictions: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """Get a single prediction by ID"""
    try:
        logger.info(f"🔍 Getting prediction with ID: {prediction_id}")
        prediction = crud.get_prediction(db, prediction_id)
        if not prediction:
            logger.warning(f"⚠️ Prediction not found: {prediction_id}")
            raise HTTPException(status_code=404, detail="Prediction not found")
        return prediction
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predictions/{prediction_id}/feedback")
def add_feedback(
    prediction_id: int,
    feedback_request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """Add feedback to a prediction"""
    try:
        logger.info(f"👍 Feedback for prediction {prediction_id}: {feedback_request.feedback}")
        prediction = crud.update_prediction_feedback(
            db, prediction_id, feedback_request.feedback
        )
        if not prediction:
            logger.warning(f"⚠️ Prediction not found for feedback: {prediction_id}")
            raise HTTPException(status_code=404, detail="Prediction not found")
        return {"message": "Feedback updated", "prediction": prediction}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────────────────────────────────────
# Utility endpoints
# ────────────────────────────────────────────────

@router.get("/stats")
def get_statistics(db: Session = Depends(get_db)):
    """Get prediction statistics"""
    try:
        logger.info("📈 Getting statistics")
        stats = crud.get_prediction_stats(db)
        return stats
    except Exception as e:
        logger.error(f"❌ Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-info")
def get_model_info():
    """Get model information"""
    try:
        logger.info("🤖 Getting model info")
        model_info = classifier.get_model_info()
        return model_info
    except Exception as e:
        logger.error(f"❌ Error getting model info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validation-rules")
def get_validation_rules():
    """Get current validation rules"""
    logger.info("📋 Getting validation rules")
    return {
        "minimum_requirements": {
            "words": 50,
            "characters": 100,
            "khmer_percentage": 50.0
        },
        "description": "For accurate classification, text should meet these minimum requirements",
        "logic": "OR condition - text must have at least 50 Khmer words OR 100 characters, AND at least 50% Khmer content",
        "recommendations": [
            "Provide at least 50 words of Khmer text",
            "Ensure text is at least 100 characters long",
            "Text should contain at least 50% Khmer characters",
            "Longer, more detailed articles yield better results"
        ]
    }


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        db.execute("SELECT 1")
        db_connected = True
    except Exception:
        db_connected = False
    
    return {
        "status": "healthy",
        "model_loaded": classifier.model is not None,
        "database": "connected" if db_connected else "disconnected",
        "validation_enabled": True,
        "minimum_requirements": {
            "words": 50,
            "characters": 100,
            "khmer_percentage": 50.0
        }
    }