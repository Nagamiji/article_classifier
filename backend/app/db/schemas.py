from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PredictionBase(BaseModel):
    text_input: str = Field(..., min_length=1, description="Text to classify")
    # Remove label_classified from base - it will be set by model

class PredictionCreate(PredictionBase):
    feedback: Optional[bool] = Field(None, description="User feedback (True=Good, False=Bad)")

class PredictionResponse(BaseModel):
    id: int
    text_input: str
    label_classified: str  # This comes from model prediction
    feedback: Optional[bool]
    created_at: datetime
    
    class Config:
        from_attributes = True

class PredictionUpdate(BaseModel):
    feedback: bool = Field(..., description="User feedback (True=Good, False=Bad)")