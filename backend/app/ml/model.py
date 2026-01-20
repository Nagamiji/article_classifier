import os
import logging
from typing import Tuple, Optional, Dict
from app.core.config import settings

logger = logging.getLogger(__name__)

# Label mapping - ONLY 6 labels (LABEL_0 to LABEL_5)
LABEL_MAPPING = {
    # Map by Khmer name
    "សេដ្ឋកិច្ច": {"code": "LABEL_0", "km": "សេដ្ឋកិច្ច", "en": "Economic"},
    "កម្សាន្ត": {"code": "LABEL_1", "km": "កម្សាន្ត", "en": "Entertainment"},
    "ជីវិត": {"code": "LABEL_2", "km": "ជីវិត", "en": "Life"},
    "នយោបាយ": {"code": "LABEL_3", "km": "នយោបាយ", "en": "Politic"},
    "កីឡា": {"code": "LABEL_4", "km": "កីឡា", "en": "Sport"},
    "បច្ចេកវិទ្យា": {"code": "LABEL_5", "km": "បច្ចេកវិទ្យា", "en": "Technology"},
    
    # Map by index (0-5 only)
    0: {"code": "LABEL_0", "km": "សេដ្ឋកិច្ច", "en": "Economic"},
    1: {"code": "LABEL_1", "km": "កម្សាន្ត", "en": "Entertainment"},
    2: {"code": "LABEL_2", "km": "ជីវិត", "en": "Life"},
    3: {"code": "LABEL_3", "km": "នយោបាយ", "en": "Politic"},
    4: {"code": "LABEL_4", "km": "កីឡា", "en": "Sport"},
    5: {"code": "LABEL_5", "km": "បច្ចេកវិទ្យា", "en": "Technology"},
}

# If model has 7 classes, map index 6 to closest match
FALLBACK_MAPPING = {
    6: {"code": "LABEL_2", "km": "ជីវិត", "en": "Life"},  # Map "Other" to "Life" as fallback
    "ផ្សេងៗ": {"code": "LABEL_2", "km": "ជីវិត", "en": "Life"},  # Map "Other" to "Life"
}

class ArticleClassifier:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.model_has_extra_class = False
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
                    
                    # Check number of labels
                    if hasattr(self.model.config, 'num_labels'):
                        num_labels = self.model.config.num_labels
                        logger.info(f"Model has {num_labels} labels")
                        
                        if num_labels > 6:
                            logger.warning(f"⚠️ Model has {num_labels} classes but only 6 are expected!")
                            logger.warning("Will map extra classes to existing labels")
                            self.model_has_extra_class = True
                    
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
                    "LABEL_5": ["tech", "computer", "phone", "software", "ai", "digital", "បច្ចេកវិទ្យា"],
                    "LABEL_4": ["sport", "game", "player", "team", "match", "win", "កីឡា"],
                    "LABEL_3": ["politic", "government", "election", "vote", "law", "នយោបាយ"],
                    "LABEL_0": ["business", "market", "stock", "company", "money", "សេដ្ឋកិច្ច"],
                    "LABEL_1": ["movie", "music", "celebrity", "film", "show", "កម្សាន្ត"],
                    "LABEL_2": ["health", "medical", "doctor", "hospital", "treatment", "life", "ជីវិត"]
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
                    return "LABEL_2", 0.65  # Default to Life category
        
        return DummyModel()
    
    def _normalize_label(self, raw_label: str, predicted_id: int) -> str:
        """Convert model output to standard label format (LABEL_0 to LABEL_5 only)"""
        # Try to map by Khmer name first
        if raw_label in LABEL_MAPPING:
            return LABEL_MAPPING[raw_label]["code"]
        
        # Try to map by ID (0-5)
        if predicted_id in LABEL_MAPPING:
            return LABEL_MAPPING[predicted_id]["code"]
        
        # Handle extra class (index 6 or "ផ្សេងៗ")
        if predicted_id >= 6 or raw_label in FALLBACK_MAPPING:
            logger.warning(f"Model predicted unexpected class: {raw_label} (id={predicted_id}), mapping to fallback")
            if predicted_id in FALLBACK_MAPPING:
                return FALLBACK_MAPPING[predicted_id]["code"]
            elif raw_label in FALLBACK_MAPPING:
                return FALLBACK_MAPPING[raw_label]["code"]
        
        # Last resort: clamp to valid range
        if predicted_id >= 6:
            clamped_id = predicted_id % 6  # Wrap around to 0-5
            logger.warning(f"Clamping invalid ID {predicted_id} to {clamped_id}")
            return f"LABEL_{clamped_id}"
        
        # Fallback
        return f"LABEL_{min(predicted_id, 5)}"
    
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
                
                # Get label name from model
                if hasattr(self.model.config, 'id2label'):
                    raw_label = self.model.config.id2label.get(predicted_class_id, f"Class_{predicted_class_id}")
                else:
                    raw_label = f"Class_{predicted_class_id}"
                
                # Normalize to LABEL_X format (LABEL_0 to LABEL_5 only)
                normalized_label = self._normalize_label(raw_label, predicted_class_id)
                
                logger.info(f"Prediction: raw={raw_label}, id={predicted_class_id}, normalized={normalized_label}, confidence={confidence:.2%}")
                
                # Warn if model predicted class 6
                if predicted_class_id >= 6:
                    logger.warning(f"⚠️ Model predicted class {predicted_class_id} ('{raw_label}'), but only 6 classes (0-5) are supported!")
                
                return normalized_label, confidence * 100
                
            else:
                # Dummy model
                return self.model.predict(text)
                
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return "LABEL_2", 0.0
    
    def get_all_probabilities(self, text: str) -> Dict[str, float]:
        """Get probabilities for all classes (LABEL_0 to LABEL_5 only)"""
        try:
            if self.model is not None and hasattr(self.model, 'config'):
                import torch
                
                inputs = self.tokenizer(
                    text, 
                    return_tensors="pt", 
                    truncation=True, 
                    max_length=512,
                    padding=True
                )
                
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
                # Build probability dict with normalized labels (LABEL_0 to LABEL_5 only)
                probs = {}
                num_classes = predictions.shape[1]
                
                # If model has 7 classes, merge class 6 probability into LABEL_2
                if num_classes > 6:
                    logger.info(f"Model has {num_classes} classes, merging extras into LABEL_2")
                    for idx in range(6):  # Only process 0-5
                        raw_label = self.model.config.id2label.get(idx, f"Class_{idx}")
                        normalized_label = self._normalize_label(raw_label, idx)
                        probs[normalized_label] = predictions[0][idx].item() * 100
                    
                    # Add class 6 probability to LABEL_2 if it exists
                    if num_classes >= 7:
                        extra_prob = predictions[0][6].item() * 100
                        probs["LABEL_2"] = probs.get("LABEL_2", 0) + extra_prob
                        logger.info(f"Added {extra_prob:.2f}% from class 6 to LABEL_2")
                else:
                    # Normal case: 6 classes
                    for idx in range(min(num_classes, 6)):
                        raw_label = self.model.config.id2label.get(idx, f"Class_{idx}")
                        normalized_label = self._normalize_label(raw_label, idx)
                        probs[normalized_label] = predictions[0][idx].item() * 100
                
                return probs
            else:
                # Return dummy probabilities
                return {
                    "LABEL_0": 15.0,
                    "LABEL_1": 15.0,
                    "LABEL_2": 20.0,
                    "LABEL_3": 15.0,
                    "LABEL_4": 15.0,
                    "LABEL_5": 20.0,
                }
        except Exception as e:
            logger.error(f"Error getting probabilities: {e}")
            return {}
    
    def get_model_info(self):
        """Get model information"""
        if self.model is not None and hasattr(self.model, 'config'):
            model_labels = []
            if hasattr(self.model.config, 'id2label'):
                for idx, label in self.model.config.id2label.items():
                    if idx < 6:  # Only show first 6 labels
                        normalized = self._normalize_label(label, idx)
                        model_labels.append(f"{normalized} ({label})")
                    else:
                        model_labels.append(f"⚠️ Extra class {idx}: {label} (will be remapped)")
            
            return {
                "model_type": "Hugging Face Transformers",
                "model_name": self.model.config._name_or_path if hasattr(self.model.config, '_name_or_path') else "Local Model",
                "model_loaded": True,
                "model_format": "safetensors",
                "num_labels": self.model.config.num_labels if hasattr(self.model.config, 'num_labels') else "Unknown",
                "expected_labels": 6,
                "labels": model_labels,
                "has_extra_classes": self.model_has_extra_class,
                "label_mapping": {k: v for k, v in LABEL_MAPPING.items() if isinstance(k, int) and k < 6}
            }
        else:
            return {
                "model_type": "Dummy Classifier",
                "model_loaded": True,
                "model_name": "Rule-based"
            }

# Global instance
classifier = ArticleClassifier()