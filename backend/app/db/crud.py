from sqlalchemy.orm import Session
from app.db import models
from decimal import Decimal

def create_prediction(
    db: Session,
    text_input: str,
    label_classified: str,
    accuracy: float,
    feedback: bool = None
):
    prediction = models.Prediction(
        text_input=text_input,
        label_classified=label_classified,
        accuracy=Decimal(str(accuracy)),
        feedback=feedback
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction

def get_predictions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Prediction).offset(skip).limit(limit).all()

def get_prediction(db: Session, prediction_id: int):
    return db.query(models.Prediction).filter(models.Prediction.id == prediction_id).first()

def update_prediction_feedback(db: Session, prediction_id: int, feedback: bool):
    prediction = get_prediction(db, prediction_id)
    if prediction:
        prediction.feedback = feedback
        db.commit()
        db.refresh(prediction)
    return prediction

def create_error_log(db: Session, error_message: str, error_type: str = "OTHER", endpoint: str = None):
    error_log = models.ErrorLog(
        error_message=error_message,
        error_type=error_type,
        endpoint=endpoint
    )
    db.add(error_log)
    db.commit()
    db.refresh(error_log)
    return error_log