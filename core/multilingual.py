"""Multilingual Detection, Script Analysis, and Cross-Lingual Translation Module.

Empowers TruthEngine to process claims across Indian languages:
- Devanagari (Hindi, Marathi, Sanskrit)
- Bengali / Assamese
- Tamil, Telugu, Kannada, Malayalam
- Gujarati, Gurmukhi (Punjabi), Urdu
- Hinglish & Latin-script transliterations
"""

import logging
import re
from typing import Tuple, Optional, Dict

logger = logging.getLogger(__name__)

# Unicode ranges for Indic scripts
INDIC_SCRIPT_RANGES = {
    "hi": (r"[\u0900-\u097F]", "Hindi / Devanagari"),
    "bn": (r"[\u0980-\u09FF]", "Bengali"),
    "pa": (r"[\u0A00-\u0A7F]", "Punjabi / Gurmukhi"),
    "gu": (r"[\u0A80-\u0AFF]", "Gujarati"),
    "ta": (r"[\u0B80-\u0BFF]", "Tamil"),
    "te": (r"[\u0C00-\u0C7F]", "Telugu"),
    "kn": (r"[\u0C80-\u0CFF]", "Kannada"),
    "ml": (r"[\u0D00-\u0D7F]", "Malayalam"),
    "ur": (r"[\u0600-\u06FF]", "Urdu / Perso-Arabic"),
}

# Common Hinglish stopwords and markers
HINGLISH_MARKERS = [
    r"\b(hai|hain|nahi|nahin|hoga|hogi|hoge|karega|karegi|karege)\b",
    r"\b(ka|ki|ke|ko|se|me|mein|par|aur|ya|bhi|toh|tha|thi|the)\b",
    r"\b(kya|kyun|kab|kaise|kaha|kahan|kitna|kitni|kitne)\b",
    r"\b(ye|yeh|wo|woh|inhe|unhe|apne|apna|apni|meri|mera|mere)\b",
    r"\b(roopaye|paise|sarkar|yojana|suchna|khabar|band|shuru)\b",
]

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "mr": "Marathi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "ml": "Malayalam",
    "pa": "Punjabi",
    "ur": "Urdu",
    "hinglish": "Hinglish (Hindi in Latin script)",
}


def detect_language(text: str) -> Tuple[str, str]:
    """Detects the language code (BCP-47 or 'hinglish') and human-readable label.

    Returns:
        (lang_code, language_name)
        e.g. ("hi", "Hindi"), ("hinglish", "Hinglish"), ("en", "English")
    """
    if not text or not text.strip():
        return "en", "English"

    s = text.strip()

    # 1. Check for native Indic scripts via Unicode regex
    for lang_code, (pattern, name) in INDIC_SCRIPT_RANGES.items():
        matches = re.findall(pattern, s)
        if len(matches) >= 3:
            return lang_code, name

    # 2. Check for Hinglish (Latin characters with Hindi phonetic tokens)
    lower_s = s.lower()
    hinglish_hits = sum(1 for pat in HINGLISH_MARKERS if re.search(pat, lower_s))
    if hinglish_hits >= 2:
        return "hinglish", "Hinglish (Hindi in Latin script)"

    # Default to English
    return "en", "English"


def translate_to_english_for_verification(claim: str, source_lang: str) -> str:
    """Translates or normalizes an Indic/Hinglish claim to English for universal web retrieval.

    Uses Hugging Face Inference API or lightweight neural translation if available,
    otherwise passes the original text (since BGE-M3 and Google Fact Check natively support Indic scripts).
    """
    if source_lang == "en" or not claim.strip():
        return claim

    # If the user has a configured HF token, we can use a translation model or LLM
    try:
        from .config import config
        if config.has_hf_token:
            from huggingface_hub import InferenceClient
            client = InferenceClient(token=config.hf_token)
            
            prompt = (
                f"Translate the following {LANGUAGE_NAMES.get(source_lang, 'Indic')} claim/query into clear English "
                f"for factual verification. Return ONLY the English translation with no quotes, notes, or preamble:\n\n{claim}"
            )
            
            resp = client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=config.hf_llm_model,
                max_tokens=150,
                temperature=0.0,
            )
            translated = (resp.choices[0].message.content or "").strip().strip('"').strip("'")
            if translated and len(translated) >= 3:
                logger.info(f"[Multilingual] Translated '{claim[:40]}' ({source_lang}) -> '{translated}'")
                return translated
    except Exception as exc:
        logger.debug(f"[Multilingual] LLM translation fallback skipped: {exc}")

    # Fallback: Return original text (BGE-M3 is multilingual and accepts Hindi/Indic directly)
    return claim
