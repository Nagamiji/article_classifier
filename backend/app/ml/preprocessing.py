# backend/app/ml/preprocessing.py

import re
import unicodedata
from typing import Dict, List

KHMER_RANGE = r"\u1780-\u17FF"
_KEEP_RE = re.compile(fr"[^{KHMER_RANGE}a-zA-Z0-9\s]", flags=re.UNICODE)

# Keep your cluster regex as fallback
_KHMER_CLUSTER_RE = re.compile(fr"[{KHMER_RANGE}][\u17B6-\u17D3\u17D7\u17DD]*", flags=re.UNICODE)

# Khmer letters matcher (used to filter tokens)
_KHMER_LETTERS_RE = re.compile(fr"[{KHMER_RANGE}]+", flags=re.UNICODE)

# Try to import Khmer word tokenizer (optional dependency)
try:
    from khmernltk import word_tokenize  # provided by package "khmer-nltk"
    _HAS_KHMER_NLTK = True
except Exception:
    word_tokenize = None
    _HAS_KHMER_NLTK = False


def remove_non_khmer_english_and_punct(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    text = _KEEP_RE.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"[A-Z]+", lambda m: m.group(0).lower(), text)
    return text


def preprocess_for_model(text: str) -> str:
    # Cleaning only, no segmentation
    return remove_non_khmer_english_and_punct(text)


def _segment_khmer_words_real(text: str) -> List[str]:
    """
    Use khmer-nltk word segmentation. Returns a list of Khmer word tokens.
    """
    if not _HAS_KHMER_NLTK:
        return []

    # word_tokenize can return tokens including spaces/punct depending on version/settings,
    # so we filter to Khmer-only tokens.
    tokens = word_tokenize(text, return_tokens=True)
    words: List[str] = []
    for tok in tokens:
        tok = tok.strip()
        if not tok:
            continue
        if _KHMER_LETTERS_RE.search(tok):
            words.append(tok)
    return words


def _segment_khmer_clusters_fallback(text: str) -> List[str]:
    """
    Your original heuristic: cluster extraction (NOT true word segmentation).
    """
    khmer_only = re.sub(fr"[^{KHMER_RANGE}\s]", " ", text)
    khmer_only = re.sub(r"\s+", " ", khmer_only).strip()
    if not khmer_only:
        return []
    clusters = _KHMER_CLUSTER_RE.findall(khmer_only)
    return [c for c in clusters if c.strip()]


def count_khmer_words(text: str, max_words: int = 512) -> Dict:
    """
    Khmer word counting:
    - Prefer true Khmer word segmentation (khmer-nltk) if available
    - Fall back to cluster heuristic if not installed
    """
    if not text:
        return {"count": 0, "words": [], "truncated": False}

    # Prefer real word segmentation
    words = _segment_khmer_words_real(text)

    # Fallback if segmenter isn't available or returns nothing
    if not words:
        words = _segment_khmer_clusters_fallback(text)

    truncated = len(words) > max_words
    limited = words[:max_words]

    return {"count": len(words), "words": limited, "truncated": truncated}
