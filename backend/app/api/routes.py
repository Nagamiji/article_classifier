from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging
import traceback

from app.db.session import get_db
from app.db import crud
from app.ml.model import classifier
from app.db.schemas import PredictionResponse
from app.ml import preprocessing

router = APIRouter()
logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────
# Schemas
# ────────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    feedback: bool


class SegmentRequest(BaseModel):
    text_input: str
    max_words: int = 512


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
# Main prediction endpoint
# ────────────────────────────────────────────────

@router.post("/predict", response_model=PredictionResponse)
def predict_article(
    text_input: str = Body(..., embed=True),
    feedback: Optional[bool] = Body(None),
    db: Session = Depends(get_db)
):
    """Classify Khmer article text"""
    try:
        processed_text = preprocessing.preprocess_for_model(text_input)
        category, confidence = classifier.predict(processed_text)

        db_prediction = crud.create_prediction(
            db=db,
            text_input=text_input,           # original text
            label_classified=category,
            accuracy=confidence,
            feedback=feedback
        )

        logger.info(f"Prediction: {category} ({confidence:.3f})")

        return db_prediction

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        crud.create_error_log(
            db=db,
            error_message=str(e),
            error_type="MODEL",
            endpoint="/predict"
        )
        raise HTTPException(status_code=500, detail=str(e))


# ────────────────────────────────────────────────
# History & feedback
# ────────────────────────────────────────────────

@router.get("/predictions", response_model=List[PredictionResponse])
def get_predictions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return crud.get_predictions(db, skip=skip, limit=limit)


@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    prediction = crud.get_prediction(db, prediction_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


@router.post("/predictions/{prediction_id}/feedback")
def add_feedback(
    prediction_id: int,
    feedback_request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    prediction = crud.update_prediction_feedback(
        db, prediction_id, feedback_request.feedback
    )
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {"message": "Feedback updated", "prediction": prediction}


# ────────────────────────────────────────────────
# Utility endpoints
# ────────────────────────────────────────────────

@router.get("/stats")
def get_statistics(db: Session = Depends(get_db)):
    return crud.get_prediction_stats(db)


@router.get("/model-info")
def get_model_info():
    return classifier.get_model_info()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    return {
        "status": "healthy",
        "model_loaded": classifier.model is not None,
        "database": "connected"
    }