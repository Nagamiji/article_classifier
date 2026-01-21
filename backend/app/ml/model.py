# D:\Year 5\S1\Advanced_programming\article_classifier\backend\app\ml\model.py
import os
import logging
import re
from typing import Tuple, Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

# Khmer Unicode range (Main Khmer + Khmer symbols)
KHMER_UNICODE_RANGE = re.compile(
    r'[\u1780-\u17FF\u19E0-\u19FF]+'
)

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
                    self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
                    
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
    
    def _calculate_khmer_percentage(self, text: str) -> float:
        """Calculate percentage of Khmer characters in text"""
        if not text or len(text.strip()) == 0:
            return 0.0
        
        # Remove whitespace for calculation
        text_no_spaces = re.sub(r'\s+', '', text)
        if len(text_no_spaces) == 0:
            return 0.0
        
        # Find all Khmer character sequences
        khmer_matches = KHMER_UNICODE_RANGE.findall(text_no_spaces)
        khmer_chars = sum(len(match) for match in khmer_matches)
        
        # Calculate percentage
        percentage = (khmer_chars / len(text_no_spaces)) * 100
        return percentage
    
    def _count_khmer_words(self, text: str) -> int:
        """Count Khmer words in text (compatible with segmentation endpoint)"""
        try:
            from app.ml import preprocessing
            # Use the same function as the segmentation endpoint
            result = preprocessing.count_khmer_words(text, max_words=10000)
            return result["count"]
        except Exception as e:
            logger.warning(f"Could not use preprocessing.count_khmer_words: {e}")
            # Fallback to simple Khmer word detection
            # Find Khmer sequences and count them as words
            khmer_sequences = KHMER_UNICODE_RANGE.findall(text)
            return len(khmer_sequences)
    
    def _validate_text_length(self, text: str, min_words: int = 50, min_chars: int = 100) -> Tuple[bool, str, Dict]:
        """Validate text length before processing - FIXED VERSION"""
        if not text or len(text.strip()) == 0:
            return False, "Text is empty", {"char_count": 0, "word_count": 0}
        
        # Count characters (including spaces)
        char_count = len(text.strip())
        
        # Count Khmer words using the same method as segmentation endpoint
        khmer_word_count = self._count_khmer_words(text)
        
        # Get total word count (all words) for reference
        total_word_count = len(text.strip().split())
        
        # FIXED LOGIC: Text should have at least min_chars characters OR min_words words
        # This matches what your error messages suggest
        if char_count < min_chars and khmer_word_count < min_words:
            return False, f"Text too short (minimum {min_words} words or {min_chars} characters required)", {
                "char_count": char_count,
                "khmer_word_count": khmer_word_count,
                "total_word_count": total_word_count,
                "min_required_chars": min_chars,
                "min_required_words": min_words,
                "validation_logic": "OR (must meet either character or word requirement)"
            }
        
        return True, "Text length is sufficient", {
            "char_count": char_count,
            "khmer_word_count": khmer_word_count,
            "total_word_count": total_word_count,
            "min_required_chars": min_chars,
            "min_required_words": min_words,
            "passed_by": "characters" if char_count >= min_chars else "words"
        }
    
    def _is_valid_khmer_text(self, text: str, min_percentage: float = 50.0) -> Tuple[bool, float, Dict]:
        """Check if text contains sufficient Khmer characters"""
        if not text or len(text.strip()) < 10:  # Minimum 10 characters
            return False, 0.0, {"error": "Text too short"}
        
        percentage = self._calculate_khmer_percentage(text)
        
        analysis = {
            "khmer_percentage": percentage,
            "text_length": len(text),
            "is_khmer_dominant": percentage >= min_percentage,
            "suggestion": "Text is suitable for classification" if percentage >= min_percentage else "Text may not be Khmer"
        }
        
        return percentage >= min_percentage, percentage, analysis
    
    def _validate_text_for_prediction(self, text: str, min_khmer_percentage: float = 50.0, min_words: int = 50, min_chars: int = 100) -> Tuple[bool, str, Dict]:
        """Complete text validation for prediction - FIXED VERSION"""
        # 1. Check text length with OR logic
        is_length_valid, length_msg, length_info = self._validate_text_length(text, min_words, min_chars)
        
        # Log what we found
        logger.info(f"📏 Length validation: chars={length_info.get('char_count', 0)}, "
                   f"khmer_words={length_info.get('khmer_word_count', 0)}, "
                   f"total_words={length_info.get('total_word_count', 0)}")
        
        if not is_length_valid:
            logger.warning(f"📏 Length validation failed: {length_msg}")
            return False, length_msg, {"validation_type": "length", **length_info}
        
        # 2. Check Khmer content
        is_khmer, khmer_percent, khmer_analysis = self._is_valid_khmer_text(text, min_khmer_percentage)
        
        # Log Khmer percentage
        logger.info(f"🔤 Khmer validation: {khmer_percent:.1f}% (min: {min_khmer_percentage}%)")
        
        if not is_khmer:
            logger.warning(f"🔤 Khmer validation failed: {khmer_percent:.1f}% < {min_khmer_percentage}%")
            return False, f"Not enough Khmer content ({khmer_percent:.1f}% < {min_khmer_percentage}% required)", {
                "validation_type": "khmer_content",
                "khmer_percentage": khmer_percent,
                "min_required_percentage": min_khmer_percentage,
                **khmer_analysis
            }
        
        # All validations passed
        logger.info("✅ All validations passed!")
        return True, "Text is valid for classification", {
            "validation_type": "all_passed",
            "char_count": length_info["char_count"],
            "khmer_word_count": length_info["khmer_word_count"],
            "total_word_count": length_info["total_word_count"],
            "khmer_percentage": khmer_percent,
            "passed_by": length_info.get("passed_by", "unknown"),
            **khmer_analysis
        }
    
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
    
    def predict(self, text: str, min_khmer_percentage: float = 50.0, min_words: int = 50, min_chars: int = 100, skip_validation: bool = False) -> Tuple[str, float, Dict]:
        """Make prediction with comprehensive text validation - FIXED VERSION"""
        # Validate text before prediction (unless skipped)
        if not skip_validation:
            is_valid, error_message, validation_info = self._validate_text_for_prediction(
                text, 
                min_khmer_percentage=min_khmer_percentage,
                min_words=min_words,
                min_chars=min_chars
            )
            
            if not is_valid:
                logger.warning(f"Text validation failed: {error_message}")
                # Return a special result for invalid text
                return "UNKNOWN", 0.0, {
                    "error": error_message,
                    "validation_info": validation_info,
                    "suggestion": f"Please provide longer Khmer text (minimum {min_words} words or {min_chars} characters with {min_khmer_percentage}% Khmer content)"
                }
        else:
            # If validation was skipped, create minimal validation info
            validation_info = {
                "validation_type": "skipped",
                "char_count": len(text),
                "khmer_word_count": self._count_khmer_words(text),
                "total_word_count": len(text.strip().split()),
                "khmer_percentage": self._calculate_khmer_percentage(text),
                "passed_by": "validation_skipped"
            }
        
        try:
            if self.model is not None and hasattr(self.model, 'config'):
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
                
                # Get predicted class and confidence (ACTUAL values)
                predicted_class_id = predictions.argmax().item()
                confidence = predictions[0][predicted_class_id].item() * 100
                
                # Get the ACTUAL label name from model
                if hasattr(self.model.config, 'id2label'):
                    actual_label = self.model.config.id2label.get(predicted_class_id, f"LABEL_{predicted_class_id}")
                else:
                    actual_label = f"LABEL_{predicted_class_id}"
                
                # Convert to standard format
                normalized_label = self._normalize_label(actual_label, predicted_class_id)
                
                logger.info(f"Actual prediction: class={actual_label} (id={predicted_class_id}), confidence={confidence:.2f}%")
                
                # Return with validation info
                return normalized_label, confidence, {
                    "validation_passed": True,
                    "validation_info": validation_info,
                    "model_used": "real_model" if self.model and hasattr(self.model, 'config') else "dummy_model",
                    "actual_model_label": actual_label
                }
                
            else:
                # Dummy model
                label, confidence = self.model.predict(text)
                return label, confidence, {
                    "validation_passed": True,
                    "validation_info": validation_info,
                    "model_used": "dummy_model"
                }
                
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return "LABEL_2", 0.0, {
                "error": str(e),
                "validation_info": validation_info
            }
    
    def predict_with_validation(self, text: str, min_khmer_percentage: float = 50.0, min_words: int = 50, min_chars: int = 100) -> Dict[str, Any]:
        """Predict with detailed validation results"""
        # First validate the text
        is_valid, error_message, validation_info = self._validate_text_for_prediction(
            text,
            min_khmer_percentage=min_khmer_percentage,
            min_words=min_words,
            min_chars=min_chars
        )
        
        if not is_valid:
            return {
                "valid": False,
                "error": error_message,
                "validation_info": validation_info,
                "category": "UNKNOWN",
                "confidence": 0.0,
                "suggestion": f"Please provide longer Khmer text (minimum {min_words} words or {min_chars} characters with {min_khmer_percentage}% Khmer content)"
            }
        
        # If valid, make prediction
        category, confidence, prediction_info = self.predict(text, min_khmer_percentage, min_words, min_chars, skip_validation=True)
        
        return {
            "valid": True,
            "category": category,
            "confidence": confidence,
            "validation_info": validation_info,
            "prediction_info": prediction_info
        }
    
    def get_all_probabilities(self, text: str, min_khmer_percentage: float = 50.0, min_words: int = 50, min_chars: int = 100) -> Dict[str, Any]:
        """Get ACTUAL probabilities with comprehensive validation"""
        # Validate text first
        is_valid, error_message, validation_info = self._validate_text_for_prediction(
            text,
            min_khmer_percentage=min_khmer_percentage,
            min_words=min_words,
            min_chars=min_chars
        )
        
        if not is_valid:
            logger.warning(f"Cannot get probabilities: {error_message}")
            return {
                "valid": False,
                "error": error_message,
                "validation_info": validation_info,
                "probabilities": {},
                "suggestion": f"Please provide longer Khmer text (minimum {min_words} words or {min_chars} characters with {min_khmer_percentage}% Khmer content)"
            }
        
        try:
            if self.model is not None and hasattr(self.model, 'config'):
                import torch
                
                # Tokenize the text
                inputs = self.tokenizer(
                    text, 
                    return_tensors="pt", 
                    truncation=True, 
                    max_length=512,
                    padding=True
                )
                
                # Get model predictions
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
                
                # Get the number of classes from the model
                num_classes = predictions.shape[1]
                
                # Create result dictionary with ACTUAL model outputs
                probabilities = {}
                
                for idx in range(num_classes):
                    # Get the actual probability from the model
                    probability = predictions[0][idx].item() * 100
                    
                    # Get the label name that the model uses
                    if hasattr(self.model.config, 'id2label'):
                        label_name = self.model.config.id2label.get(idx, f"LABEL_{idx}")
                    else:
                        label_name = f"LABEL_{idx}"
                    
                    # Store the actual probability
                    probabilities[label_name] = probability
                
                logger.info(f"Actual model outputs: {probabilities}")
                
                return {
                    "valid": True,
                    "probabilities": probabilities,
                    "validation_info": validation_info,
                    "model_used": "real_model"
                }
                    
            else:
                # If using dummy model, return simple fixed probabilities
                return {
                    "valid": True,
                    "probabilities": {
                        "LABEL_0": 16.67,
                        "LABEL_1": 16.67,
                        "LABEL_2": 16.67,
                        "LABEL_3": 16.67,
                        "LABEL_4": 16.67,
                        "LABEL_5": 16.67,
                    },
                    "validation_info": validation_info,
                    "model_used": "dummy_model"
                }
                
        except Exception as e:
            logger.error(f"Error getting probabilities: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "valid": False,
                "error": str(e),
                "validation_info": validation_info,
                "probabilities": {}
            }
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text without making prediction (for debugging)"""
        is_khmer, percentage, analysis = self._is_valid_khmer_text(text)
        
        # Count characters by type
        total_chars = len(text)
        khmer_chars = sum(len(match) for match in KHMER_UNICODE_RANGE.findall(text))
        non_khmer_chars = total_chars - khmer_chars
        
        # Get different word counts
        total_word_count = len(text.strip().split())
        khmer_word_count = self._count_khmer_words(text)
        
        # Check if text would pass validation with OR logic
        char_count = len(text)
        length_valid = (char_count >= 100) or (khmer_word_count >= 50)
        khmer_valid = percentage >= 50.0
        
        # Determine which requirement would be passed
        passed_by = []
        if char_count >= 100:
            passed_by.append("characters")
        if khmer_word_count >= 50:
            passed_by.append("khmer_words")
        
        return {
            "text_length": total_chars,
            "total_word_count": total_word_count,
            "khmer_word_count": khmer_word_count,
            "khmer_percentage": percentage,
            "khmer_characters": khmer_chars,
            "non_khmer_characters": non_khmer_chars,
            "is_khmer": is_khmer,
            "length_validation": {
                "valid": length_valid,
                "passed_by": passed_by if passed_by else ["none"],
                "char_count": char_count,
                "min_characters": 100,
                "khmer_word_count": khmer_word_count,
                "min_words": 50,
                "logic": "OR (must meet either character or word requirement)"
            },
            "khmer_validation": {
                "valid": khmer_valid,
                "khmer_percentage": percentage,
                "required_percentage": 50.0
            },
            "would_pass_validation": length_valid and khmer_valid,
            "text_preview": text[:100] + "..." if len(text) > 100 else text
        }
    
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
                "label_mapping": {k: v for k, v in LABEL_MAPPING.items() if isinstance(k, int) and k < 6},
                "khmer_detection": "Enabled",
                "min_khmer_percentage": "50% (configurable)",
                "text_validation": {
                    "min_words": 50,
                    "min_characters": 100,
                    "description": "Text must be at least 50 words OR 100 characters",
                    "logic": "OR condition (meets either requirement)",
                    "khmer_word_count_used": True
                }
            }
        else:
            return {
                "model_type": "Dummy Classifier",
                "model_loaded": True,
                "model_name": "Rule-based",
                "khmer_detection": "Enabled",
                "min_khmer_percentage": "50% (configurable)",
                "text_validation": {
                    "min_words": 50,
                    "min_characters": 100,
                    "description": "Text must be at least 50 words OR 100 characters",
                    "logic": "OR condition (meets either requirement)",
                    "khmer_word_count_used": True
                }
            }

# Global instance
classifier = ArticleClassifier()