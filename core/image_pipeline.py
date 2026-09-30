"""Image Verification Pipeline for Multimodal Misinformation Analysis."""

import base64
import io
import logging
import time
from typing import Optional
from PIL import Image

from .schemas import (
    AnalysisResult,
    AssessmentVerdict,
    ClaimType,
)
from .image_ocr import extract_text_from_image_bytes
from .pipeline import analyze_claim_single

logger = logging.getLogger(__name__)


def generate_thumbnail_data_url(image_bytes: bytes, max_dim: int = 400) -> Optional[str]:
    """Generates a compact base64 data URI thumbnail of the input image for UI preview."""
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        pil_img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=75)
        b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{b64}"
    except Exception as exc:
        logger.debug(f"Failed to generate image preview data URL: {exc}")
        return None


def analyze_image(
    image_bytes: bytes,
    filename: Optional[str] = None,
    user_question: Optional[str] = None,
) -> AnalysisResult:
    """End-to-end multimodal verification pipeline for an uploaded image.

    1. Extracts text from the image using the OCR engine.
    2. Resolves claim proposition between extracted text and optional user question.
    3. Executes evidence-grounded verification pipeline.
    4. Attaches image thumbnail and OCR extraction metadata to the result.
    """
    start_time = time.time()
    logger.info(f"Beginning image analysis for file: {filename or 'unnamed_image'}")

    # Generate preview thumbnail for the UI
    preview_url = generate_thumbnail_data_url(image_bytes)

    # Step 1: Run OCR text extraction
    extracted_text, ocr_err = extract_text_from_image_bytes(image_bytes)
    logger.info(f"OCR extracted text: '{extracted_text}' (error: {ocr_err})")

    clean_question = (user_question or "").strip()

    # Step 2: Formulate claim to verify
    claim_to_verify = ""
    if clean_question and extracted_text:
        lower_q = clean_question.lower().strip(" ?.")
        inquiry_starters = ("is", "did", "was", "has", "can", "will", "does", "are", "were", "what", "why", "fact check", "true", "real")
        if any(lower_q.startswith(w) for w in inquiry_starters) or len(extracted_text.split()) >= 3:
            claim_to_verify = extracted_text
        else:
            claim_to_verify = f"{clean_question}: {extracted_text}"
    elif extracted_text:
        claim_to_verify = extracted_text
    elif clean_question:
        claim_to_verify = clean_question
    else:
        # Neither readable text nor a user question was provided
        elapsed = round(time.time() - start_time, 2)
        return AnalysisResult(
            claim=filename or "Uploaded Image",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.INSUFFICIENT_EVIDENCE,
            verdict_symbol="🟡",
            verdict_title="INSUFFICIENT EVIDENCE",
            confidence_score=0.2,
            explanation=(
                "No legible text was detected in the uploaded image, and no specific question was asked. "
                "Please upload an image containing readable text (such as a screenshot, document, or flyer) "
                "or specify a question to verify."
            ),
            supporting_evidence=[],
            contradicting_evidence=[],
            evidence_limitations=["No OCR text extracted from image payload."],
            all_sources=[],
            latency_seconds=elapsed,
            mode="image",
            user_question=clean_question or None,
            extracted_image_text=None,
            image_preview=preview_url,
            targeted_answer="No readable text detected in image to verify.",
        )

    # Step 3: Run pipeline analysis on the formulated claim
    analysis_res = analyze_claim_single(claim_to_verify)

    elapsed = round(time.time() - start_time, 2)

    # Step 4: Augment result with image metadata
    return AnalysisResult(
        claim=claim_to_verify,
        claim_type=analysis_res.claim_type,
        verdict=analysis_res.verdict,
        verdict_symbol=analysis_res.verdict_symbol,
        verdict_title=analysis_res.verdict_title,
        confidence_score=analysis_res.confidence_score,
        explanation=analysis_res.explanation,
        supporting_evidence=analysis_res.supporting_evidence,
        contradicting_evidence=analysis_res.contradicting_evidence,
        evidence_limitations=analysis_res.evidence_limitations,
        all_sources=analysis_res.all_sources,
        relevant_images=analysis_res.relevant_images,
        latency_seconds=elapsed,
        mode="image",
        user_question=clean_question or None,
        extracted_image_text=extracted_text or None,
        image_preview=preview_url,
        targeted_answer=analysis_res.targeted_answer,
    )
