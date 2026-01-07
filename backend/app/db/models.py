from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    text_input = Column(Text, nullable=False)
    label_classified = Column(String(255), nullable=False)
    feedback = Column(Boolean, default=None, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Prediction(id={self.id}, label='{self.label_classified}')>"


class ErrorLog(Base):
    __tablename__ = "error_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    error_message = Column(Text, nullable=False)
    error_type = Column(String(50))  # 'MODEL', 'DB', 'API', 'OTHER'
    endpoint = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<ErrorLog(id={self.id}, type='{self.error_type}', message='{self.error_message[:50]}...')>"