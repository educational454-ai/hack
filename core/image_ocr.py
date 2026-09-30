"""Image OCR and Text Extraction Engine for Multimodal Misinformation Analysis.

Supports:
1. Native Windows WinRT OCR (Windows.Media.Ocr) - offline, fast, zero external dependencies.
2. Pytesseract OCR - cross-platform fallback when Tesseract binary is available.
3. Fallback text extraction & normalization.
"""

import asyncio
import io
import logging
import os
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Dedicated thread pool for OCR operations so WinRT async tasks never conflict with FastAPI event loop
_ocr_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ocr_worker")


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


def _run_winrt_ocr_sync(image_path: str) -> Optional[str]:
    """Runs Windows.Media.Ocr synchronously in an isolated thread with its own event loop."""
    try:
        import winrt.windows.storage as ws
        import winrt.windows.graphics.imaging as wgi
        import winrt.windows.media.ocr as wmo

        async def _async_ocr():
            abs_path = os.path.abspath(image_path)
            storage_file = await ws.StorageFile.get_file_from_path_async(abs_path)
            stream = await storage_file.open_async(ws.FileAccessMode.READ)
            decoder = await wgi.BitmapDecoder.create_async(stream)
            software_bitmap = await decoder.get_software_bitmap_async()

            engine = wmo.OcrEngine.try_create_from_user_profile_languages()
            if engine is None:
                import winrt.windows.globalization as wg
                engine = wmo.OcrEngine.try_create_from_language(wg.Language("en-US"))

            if engine is None:
                return None

            ocr_res = await engine.recognize_async(software_bitmap)
            return ocr_res.text

        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            extracted = loop.run_until_complete(_async_ocr())
            return extracted
        finally:
            loop.close()
    except Exception as exc:
        logger.warning(f"WinRT OCR encountered error: {exc}")
        return None


def _run_pytesseract_ocr(pil_img: Image.Image) -> Optional[str]:
    """Runs pytesseract OCR if tesseract executable is installed and available."""
    try:
        import pytesseract
        text = pytesseract.image_to_string(pil_img)
        if text and text.strip():
            return text.strip()
    except Exception as exc:
        logger.debug(f"Pytesseract not available or failed: {exc}")
    return None


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
        (extracted_text, error_message_if_any)
    """
    if not image_bytes:
        return "", "Empty image payload provided."

    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
    except Exception as exc:
        return "", f"Invalid image format: {exc}"

    processed_img = preprocess_image_for_ocr(pil_image)

    # 1. Primary: Try Windows WinRT OCR via temporary file
    extracted_text = None
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        processed_img.save(tmp_path, format="PNG")
        future = _ocr_executor.submit(_run_winrt_ocr_sync, tmp_path)
        extracted_text = future.result(timeout=15)
    except Exception as exc:
        logger.warning(f"Primary WinRT OCR execution failed: {exc}")
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

    # 2. Fallback: Try pytesseract
    if not extracted_text or not extracted_text.strip():
        extracted_text = _run_pytesseract_ocr(processed_img)

    clean_text = clean_extracted_ocr_text(extracted_text or "")
    if not clean_text:
        return "", "No readable text detected in image."

    return clean_text, None
