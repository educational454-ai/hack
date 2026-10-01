"""Image OCR and Text Extraction Engine for Multimodal Misinformation Analysis.

Supports:
1. Primary: RapidOCR (rapidocr-onnxruntime) - cross-platform, fast, pure Python wheel + ONNX runtime.
2. Fallback: Pytesseract OCR - when tesseract binary executable is installed on system.
3. Fallback text extraction & normalization.
"""

import io
import logging
import os
import re
from typing import Optional, Tuple
from PIL import Image, ImageOps

from .config import config

logger = logging.getLogger(__name__)

# Lazy singleton for RapidOCR engine
_rapid_ocr_engine = None


def get_rapid_ocr_engine():
    """Lazily initializes and caches the RapidOCR engine instance."""
    global _rapid_ocr_engine
    if _rapid_ocr_engine is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _rapid_ocr_engine = RapidOCR()
            logger.info("Successfully initialized RapidOCR engine.")
        except Exception as exc:
            logger.warning(f"Failed to initialize RapidOCR engine: {exc}")
            _rapid_ocr_engine = False
    return _rapid_ocr_engine if _rapid_ocr_engine is not False else None


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """Preprocesses a PIL image to maximize OCR recognition accuracy."""
    # Convert RGBA / P / CMYK to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    # If image is very small, upscale it for better letter edge detection
    w, h = image.size
    if w < 600 or h < 300:
        scale = max(600 / max(w, 1), 300 / max(h, 1))
        scale = min(scale, 4.0)
        new_w = int(w * scale)
        new_h = int(h * scale)
        image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Auto contrast
    try:
        image = ImageOps.autocontrast(image)
    except Exception:
        pass

    return image


def _run_rapid_ocr(image_bytes: bytes) -> Tuple[Optional[str], Optional[str]]:
    """Runs RapidOCR on raw image bytes."""
    engine = get_rapid_ocr_engine()
    if engine is None:
        return None, "RapidOCR engine not available."

    try:
        ocr_res, _ = engine(image_bytes)
        if ocr_res:
            lines = [line[1] for line in ocr_res if len(line) >= 2 and line[1]]
            text = " ".join(lines).strip()
            if text:
                return text, None
        return "", None
    except Exception as exc:
        logger.warning(f"RapidOCR execution encountered error: {exc}")
        return None, f"RapidOCR execution error: {exc}"


def _run_pytesseract_ocr(pil_img: Image.Image) -> Tuple[Optional[str], Optional[str]]:
    """Runs pytesseract OCR if tesseract executable is installed on system."""
    try:
        import pytesseract
        text = pytesseract.image_to_string(pil_img)
        if text and text.strip():
            return text.strip(), None
        return "", None
    except Exception as exc:
        logger.debug(f"Pytesseract execution failed: {exc}")
        return None, f"Pytesseract error: {exc}"


def clean_extracted_ocr_text(raw_text: str) -> str:
    """Cleans OCR artifacts, UI noise, timestamps, and redundant whitespace."""
    if not raw_text:
        return ""

    lines = raw_text.splitlines()
    cleaned_lines = []

    # Ignore common screenshot header/footer noise (battery, wifi, time patterns)
    noise_patterns = [
        r"^\s*(\d{1,2}:\d{2}(\s*[AaPp][Mm])?|\d{1,3}%|LTE|5G|4G|WiFi|VoLTE)\s*$",
        r"^\s*(battery|signal|carrier)\s*$",
        r"^[_\-=~*#\s]{3,}$",
    ]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if any(re.match(pat, stripped, re.IGNORECASE) for pat in noise_patterns):
            continue
        cleaned_lines.append(stripped)

    joined = " ".join(cleaned_lines)
    # Collapse multiple whitespaces
    joined = re.sub(r"\s+", " ", joined).strip()
    return joined


def extract_text_from_image_bytes(image_bytes: bytes) -> Tuple[str, Optional[str]]:
    """Extracts text from raw image bytes using available OCR engines.

    Returns:
        (extracted_text, error_message_or_status)
    """
    if not image_bytes:
        return "", "Empty image payload provided."

    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
    except Exception as exc:
        return "", f"Invalid image format: {exc}"

    processed_img = preprocess_image_for_ocr(pil_image)

    # Convert processed PIL image back to bytes for engines accepting raw bytes
    buf = io.BytesIO()
    processed_img.save(buf, format="PNG")
    processed_bytes = buf.getvalue()

    # 1. Primary: RapidOCR (rapidocr-onnxruntime)
    text, err = _run_rapid_ocr(processed_bytes)
    if text:
        clean_text = clean_extracted_ocr_text(text)
        if clean_text:
            return clean_text, None

    # 2. Fallback: Pytesseract
    text_tess, err_tess = _run_pytesseract_ocr(processed_img)
    if text_tess:
        clean_text = clean_extracted_ocr_text(text_tess)
        if clean_text:
            return clean_text, None

    # Determine if failure was due to no text vs. no engine available
    if err and "not available" in err and err_tess and "error" in str(err_tess):
        return "", "Image text extraction is currently unavailable because no OCR backend is configured."

    return "", "No readable text detected in image."
