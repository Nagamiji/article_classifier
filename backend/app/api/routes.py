from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db.session import get_db
from app.db import crud
from app.ml.model import classifier
from app.db.schemas import PredictionResponse
import logging

from app.ml import preprocessing

router = APIRouter()
logger = logging.getLogger(__name__)

# Schema for feedback request
class FeedbackRequest(BaseModel):
    feedback: bool

#  Add new /segment endpoint and preprocessing pipeline 
class SegmentRequest(BaseModel):
    text_input: str
    max_words: int = 512

@router.post("/segment")
def segment_text(payload: SegmentRequest):
    """
    Endpoint: /api/v1/segment
    Returns Khmer word count, up to `max_words` Khmer clusters, and a truncated flag.
    """
    try:
        cleaned = preprocessing.remove_non_khmer_english_and_punct(payload.text_input)
        result = preprocessing.count_khmer_words(cleaned, max_words=payload.max_words)
        return {
            "khmer_word_count": result["count"],
            "khmer_words": result["words"],
            "truncated": result["truncated"],
            "cleaned_text": cleaned,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/predict", response_model=PredictionResponse)
def predict_article(
    text_input: str = Body(..., embed=True),  # Accept just text_input as raw body
    feedback: Optional[bool] = Body(None),    # Optional feedback in the same body
    db: Session = Depends(get_db)
):
    """Make a prediction for article text"""
    try:
        # Preprocess for model (cleaning only, NO segmentation)
        processed_text = preprocessing.preprocess_for_model(text_input)

        # Get prediction from ML model using processed text
        category, confidence = classifier.predict(processed_text)
       
        # Save to database (store original text_input for traceability)
        db_prediction = crud.create_prediction(
            db=db,
            text_input=text_input,
            label_classified=category,
            feedback=feedback
        )
       
        logger.info(f"Prediction made: {category} with {confidence:.2f}% confidence")
       
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


@router.get("/predictions", response_model=List[PredictionResponse])
def get_predictions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all predictions"""
    predictions = crud.get_predictions(db, skip=skip, limit=limit)
    return predictions


@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
def get_prediction(prediction_id: int, db: Session = Depends(get_db)):
    """Get a specific prediction"""
    prediction = crud.get_prediction(db, prediction_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


@router.post("/predictions/{prediction_id}/feedback")
def add_feedback(
    prediction_id: int, 
    feedback_request: FeedbackRequest,  # ✅ Now expects JSON body with feedback field
    db: Session = Depends(get_db)
):
    """Add feedback to a prediction"""
    prediction = crud.update_prediction_feedback(db, prediction_id, feedback_request.feedback)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return {"message": "Feedback added", "prediction": prediction}


@router.get("/stats")
def get_statistics(db: Session = Depends(get_db)):
    """Get prediction statistics"""
    stats = crud.get_prediction_stats(db)
    return stats


@router.get("/model-info")
def get_model_info():
    """Get model information"""
    return classifier.get_model_info()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": classifier.model is not None,
        "database": "connected"
    }