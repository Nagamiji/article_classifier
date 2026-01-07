import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API
    API_V1_PREFIX: str = "/api/v1"  # ⭐ This must match router prefix
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@postgres:5432/article_classifier"
    )
    
    # ML Model
    MODEL_CACHE_DIR: str = os.getenv("MODEL_CACHE_DIR", "/app/ml/artifacts")
    
    class Config:
        env_file = ".env"

settings = Settings()