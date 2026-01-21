from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from app.core.config import settings
from app.api.routes import router as api_router  # IMPORTANT
from app.db.session import engine
from app.db import models

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Khmer Article Classifier",
    description="Classify Khmer news articles using ML",
    version="1.0.0"
)

# Add CORS
# In backend/app/main.py, update CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:5500", 
        "http://127.0.0.1:5500",
        "http://localhost",  # For nginx
        "http://127.0.0.1",  # For nginx
        "http://localhost:80",
        "http://127.0.0.1:80",
        "*"  # Keep wildcard as fallback
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """Initialize on startup"""
    logger.info("Starting Article Classifier API")
    
    # Create database tables
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Database error: {e}")
        logger.warning("Database connection failed, but API will continue")
    
    # Import and log model info
    from app.ml.model import classifier
    model_info = classifier.get_model_info()
    logger.info(f"Model loaded: {model_info}")

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "message": "Khmer Article Classifier API",
        "model": "xlm-r-khmer-news-classification",
        "status": "running",
        "endpoints": ["/docs", "/api/predict", "/api/health"]
    }

@app.get("/health")
def health():
    from app.ml.model import classifier
    return {
        "status": "healthy",
        "model_loaded": classifier.model is not None
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)