"""
Khmer text preprocessing with khmernltk support

File: backend/app/ml/preprocessing.py
"""

import re
import logging

logger = logging.getLogger(__name__)

def remove_non_khmer_english_and_punct(text: str) -> str:
    """
    Remove special characters but keep Khmer, English, numbers, and basic punctuation
    
    Args:
        text: Input text to clean
        
    Returns:
        Cleaned text with only valid characters
    """
    if not text:
        return ""
    
    # Keep: 
    # - Khmer Unicode range: U+1780-U+17FF (main Khmer block)
    # - Khmer Symbols: U+19E0-U+19FF (extended Khmer symbols)
    # - Zero-width joiner/non-joiner: U+200B-U+200D (for proper Khmer rendering)
    # - English letters: a-zA-Z
    # - Numbers: 0-9
    # - Spaces and basic punctuation: .,!?។៕
    # NOTE: Fixed the zero-width character range syntax
    pattern = r'[^\u1780-\u17FF\u19E0-\u19FF\u200B-\u200Da-zA-Z0-9\s.,!?។៕]'
    cleaned = re.sub(pattern, '', text)
    
    # Normalize whitespace (multiple spaces → single space)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    logger.debug(f"Original text length: {len(text)}, Cleaned text length: {len(cleaned)}")
    
    return cleaned


def count_khmer_words(text: str, max_words: int = 512) -> dict:
    """
    Count and segment Khmer words using khmernltk
    
    This function uses khmernltk's word_tokenize for accurate Khmer word segmentation.
    Falls back to simple space-based splitting if khmernltk is not available.
    
    Args:
        text: Khmer text to segment
        max_words: Maximum number of words to return
        
    Returns:
        dict with keys:
            - count: Number of words/tokens
            - words: List of segmented words
            - truncated: Boolean indicating if text was truncated
    """
    if not text or not text.strip():
        logger.warning("Empty or whitespace-only text received")
        return {
            "count": 0,
            "words": [],
            "truncated": False
        }
    
    try:
        # CRITICAL: Try to use khmernltk for proper Khmer word segmentation
        try:
            from khmernltk import word_tokenize
            
            logger.info("✅ Using khmernltk for Khmer word segmentation")
            
            # Tokenize using khmernltk - this properly segments Khmer words!
            words = word_tokenize(text)
            
            logger.info(f"khmernltk segmented text into {len(words)} words")
            logger.debug(f"First 5 words: {words[:5] if len(words) > 5 else words}")
            
            # Filter out empty strings and whitespace-only tokens
            words = [w.strip() for w in words if w.strip()]
            
            original_count = len(words)
            
            # Check if truncation is needed
            truncated = original_count > max_words
            
            if truncated:
                words = words[:max_words]
                logger.info(f"✂️ Text truncated from {original_count} to {max_words} words")
            
            return {
                "count": len(words),
                "words": words,
                "truncated": truncated
            }
            
        except ImportError as e:
            logger.error(f"❌ khmernltk not installed: {e}")
            logger.error("⚠️ FALLING BACK TO SPACE-BASED COUNTING - This is INACCURATE for Khmer!")
            logger.error("⚠️ Please install khmernltk: pip install khmernltk")
            logger.error(f"⚠️ Input text preview: {text[:100]}...")
            
            # Fallback: Split by spaces (INACCURATE for Khmer!)
            words = text.split()
            words = [w.strip() for w in words if w.strip()]
            
            logger.warning(f"Fallback produced {len(words)} words (space-based)")
            
            original_count = len(words)
            truncated = original_count > max_words
            
            if truncated:
                words = words[:max_words]
                logger.info(f"Fallback: Text truncated from {original_count} to {max_words} words")
            
            return {
                "count": len(words),
                "words": words,
                "truncated": truncated
            }
            
    except Exception as e:
        logger.error(f"❌ Error in count_khmer_words: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Emergency fallback
        words = text.split()
        words = [w.strip() for w in words if w.strip()]
        
        return {
            "count": min(len(words), max_words),
            "words": words[:max_words],
            "truncated": len(words) > max_words
        }


def preprocess_for_model(text: str) -> str:
    """
    Preprocess text for model prediction
    
    This function cleans the text but does NOT segment it into words,
    as the transformer model does its own tokenization.
    
    Args:
        text: Raw input text
        
    Returns:
        Cleaned text ready for model input
    """
    if not text:
        return ""
    
    # Step 1: Remove special characters (keep Khmer, English, numbers, basic punctuation)
    cleaned = remove_non_khmer_english_and_punct(text)
    
    logger.debug(f"After cleaning: '{cleaned}'")
    
    # Step 2: Normalize whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # Step 3: For Khmer text, remove spaces between Khmer characters
    # This is important because some Khmer text has spaces between words,
    # but the model expects continuous Khmer text
    # Pattern: space between Khmer characters → remove space
    cleaned = re.sub(r'(?<=[\u1780-\u17FF])\s+(?=[\u1780-\u17FF])', '', cleaned)
    
    logger.info(f"Preprocessed text length: {len(cleaned)} characters")
    
    return cleaned


def segment_for_display(text: str, max_words: int = 50) -> str:
    """
    Segment text for display purposes (e.g., preview in UI)
    
    Args:
        text: Text to segment
        max_words: Maximum words to include
        
    Returns:
        Segmented text string (first max_words words)
    """
    result = count_khmer_words(text, max_words=max_words)
    
    if result["truncated"]:
        return ' '.join(result["words"]) + '...'
    else:
        return ' '.join(result["words"])