import os
import logging
from typing import Tuple, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class ArticleClassifier:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load pre-downloaded Hugging Face model"""
        try:
            model_path = settings.MODEL_CACHE_DIR
            
            if not os.path.exists(model_path):
                logger.error(f"Model directory not found: {model_path}")
                self.model = self._create_dummy_model()
                return
            
            # Check for model files
            files = os.listdir(model_path)
            logger.info(f"Found {len(files)} files in model directory")
            
            # Check for safetensors file (which you have)
            has_safetensors = any(f.endswith('.safetensors') for f in files)
            has_config = 'config.json' in files
            
            if has_safetensors and has_config:
                # Load transformers model with safetensors
                try:
                    from transformers import AutoModelForSequenceClassification, AutoTokenizer
                    
                    logger.info("Loading Hugging Face model with safetensors...")
                    
                    # Load tokenizer
                    self.tokenizer = AutoTokenizer.from_pretrained(model_path)
                    
                    # Load model with safetensors
                    self.model = AutoModelForSequenceClassification.from_pretrained(
                        model_path,
                        local_files_only=True  # Important: use local files only
                    )
                    
                    # Move model to evaluation mode
                    self.model.eval()
                    
                    logger.info("✅ Hugging Face model loaded successfully!")
                    logger.info(f"Model type: {type(self.model).__name__}")
                    logger.info(f"Tokenizer type: {type(self.tokenizer).__name__}")
                    
                    # Log model info
                    if hasattr(self.model.config, 'id2label'):
                        labels = list(self.model.config.id2label.values())
                        logger.info(f"Available labels: {labels}")
                    
                except ImportError as e:
                    logger.error(f"Transformers not installed: {e}")
                    self.model = self._create_dummy_model()
                    
            else:
                logger.warning("No model.safetensors found, using dummy model")
                self.model = self._create_dummy_model()
                
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.model = self._create_dummy_model()
    
    def _create_dummy_model(self):
        """Fallback dummy model"""
        class DummyModel:
            def predict(self, text: str) -> Tuple[str, float]:
                text_lower = text.lower()
                categories = {
                    "បច្ចេកវិទ្យា": ["tech", "computer", "phone", "software", "ai", "digital"],
                    "កីឡា": ["sport", "game", "player", "team", "match", "win"],
                    "នយោបាយ": ["politic", "government", "election", "vote", "law"],
                    "អាជីវកម្ម": ["business", "market", "stock", "company", "money"],
                    "កម្សាន្ត": ["movie", "music", "celebrity", "film", "show"],
                    "សុខភាព": ["health", "medical", "doctor", "hospital", "treatment"]
                }
                
                scores = {}
                for category, keywords in categories.items():
                    score = sum(1 for kw in keywords if kw in text_lower)
                    scores[category] = score
                
                # Get best match
                if sum(scores.values()) > 0:
                    best = max(scores.items(), key=lambda x: x[1])
                    return best[0], 0.75 + (best[1] * 0.05)
                else:
                    return "ផ្សេងៗ", 0.65
        
        return DummyModel()
    
    def predict(self, text: str) -> Tuple[str, float]:
        """Make prediction"""
        try:
            if self.model is not None and hasattr(self.model, 'config'):
                # Real Hugging Face model
                import torch
                
                # Tokenize
                inputs = self.tokenizer(
                    text, 
                    return_tensors="pt", 
                    truncation=True, 
                    max_length=512,
                    padding=True
                )
                
                # Predict
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
                # Get predicted class
                predicted_class_id = predictions.argmax().item()
                confidence = predictions[0][predicted_class_id].item()
                
                # Get label name
                if hasattr(self.model.config, 'id2label'):
                    label = self.model.config.id2label.get(predicted_class_id, f"Class_{predicted_class_id}")
                else:
                    label = f"Class_{predicted_class_id}"
                
                return label, confidence * 100
                
            else:
                # Dummy model
                return self.model.predict(text)
                
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return "កំហុស", 0.0
    
    def get_model_info(self):
        """Get model information"""
        if self.model is not None and hasattr(self.model, 'config'):
            return {
                "model_type": "Hugging Face Transformers",
                "model_name": self.model.config._name_or_path if hasattr(self.model.config, '_name_or_path') else "Local Model",
                "model_loaded": True,
                "model_format": "safetensors",
                "num_labels": self.model.config.num_labels if hasattr(self.model.config, 'num_labels') else "Unknown",
                "labels": list(self.model.config.id2label.values()) if hasattr(self.model.config, 'id2label') else []
            }
        else:
            return {
                "model_type": "Dummy Classifier",
                "model_loaded": True,
                "model_name": "Rule-based"
            }

# Global instance
classifier = ArticleClassifier()