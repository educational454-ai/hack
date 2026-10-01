"""Image Verification Pipeline for Multimodal Misinformation Analysis."""

import base64
import io
import logging
import os
import re
import time
from typing import Optional, Tuple
from PIL import Image

from .config import config
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


def classify_question_intent(question: Optional[str]) -> str:
    """Classifies user question into generic intent categories:

    - 'text_extraction': User asks to extract, read, transcribe, display, or identify visible text/writing.
    - 'fact_check_verify': User wants to verify the truth of the image content/claim.
    - 'visual_question': User asks about visual attributes, objects, colors, or spatial geometry.
    - 'specific_question': User asks a specific non-generic question about a claim or topic.
    """
    q = (question or "").strip().lower()
    if not q:
        return "fact_check_verify"

    # Clean punctuation for pattern matching
    q_clean = re.sub(r"[^\w\s]", "", q).strip()

    # 1. Text extraction intent (MANDATORY: Check FIRST before visual patterns)
    if q_clean in (
        "ocr", "transcribe", "read text", "extract text", "get text",
        "show text", "read this", "transcribe this", "read writing",
        "extract writing", "show writing", "read image", "transcribe image"
    ):
        return "text_extraction"

    # Verbs paired with text targets or standalone transcribe/ocr verbs
    if re.search(r"\b(transcribe|ocr)\b", q_clean):
        return "text_extraction"

    if re.search(
        r"\b(extract|read|get|show|display|tell|copy|parse|scan|identify|recognize)\s+.*?\b(text|words|writing|letters|caption|script)\b",
        q_clean,
    ):
        return "text_extraction"

    if re.search(r"\bwhat\s+.*?\b(text|words|writing|script|caption)\b", q_clean):
        return "text_extraction"

    if re.search(r"\bwhat\s+does\s+.*?\bsay\b", q_clean):
        return "text_extraction"

    if re.search(r"\bwhat\s+is\s+written\b", q_clean):
        return "text_extraction"

    if re.search(r"\b(read|tell|show)\s+what\s+is\s+written\b", q_clean):
        return "text_extraction"

    # 2. Fact-check / verification generic intent
    generic_verify_phrases = {
        "verify", "fact check", "factcheck", "check", "is this true", "is it true",
        "is this real", "is it real", "is this fake", "is it fake", "fact check this",
        "verify this", "check this", "what does this image claim", "what claim is this",
        "true or false", "real or fake", "is this claim true", "confirm", "legit",
        "is this legit", "is this claim real", "fact check this claim", "is it verified",
        "is this accurate", "is it accurate", "can you fact check this", "can you verify this",
        "check whether this is true", "verify if this is true", "fact check whether this is true"
    }
    if q_clean in generic_verify_phrases:
        return "fact_check_verify"

    # Short prefix matches (e.g., "can you verify", "fact check if...", "is this true that...")
    if re.match(r"^(can you\s+)?(verify|fact\s*check|check)\b", q_clean) and len(q_clean.split()) <= 5:
        return "fact_check_verify"
    if re.match(r"^is\s+(this|it)\s+(true|real|fake|legit|accurate)\b", q_clean) and len(q_clean.split()) <= 5:
        return "fact_check_verify"

    # 3. Visual question intent
    visual_patterns = [
        r"\b(square|round|circle|triangular|rectangular|tall|wide|big|small)\b",
        r"\b(what|which)\s+.*?\b(color|colour|shape|object|animal|person|car|building|logo|background|scene)\b",
        r"\bhow\s+many\b",
        r"\b(is there|are there|do you see|can you see)\s+(a|an|any|the)\b",
        r"\bwhat\s+(is|are)\s+(shown|visible|happening|in this|in the photo|in the image)\b",
        r"\bwho\s+is\b",
        r"\bwhat\s+does\s+.*?\blook\s+like\b",
        r"\bdescribe\s+.*?\b(image|photo|picture|object|scene)\b",
    ]
    if any(re.search(pat, q_clean) for pat in visual_patterns):
        return "visual_question"

    # Default to specific question
    return "specific_question"


def analyze_with_multimodal_vision(image_bytes: bytes, question: str) -> Optional[str]:
    """Runs genuine multimodal vision inference using Hugging Face InferenceClient if configured."""
    if not config.has_hf_token:
        return None

    try:
        from huggingface_hub import InferenceClient
        vision_model = os.getenv("HF_VISION_MODEL", "meta-llama/Llama-3.2-11B-Vision-Instruct").strip()
        client = InferenceClient(token=config.hf_token)

        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{b64_img}"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": question}
                ]
            }
        ]

        logger.info(f"Calling HF Multimodal Vision Model '{vision_model}' for visual question: '{question}'...")
        response = client.chat_completion(
            messages=messages,
            model=vision_model,
            max_tokens=300,
            temperature=0.1
        )
        content = response.choices[0].message.content or ""
        if content.strip():
            logger.info(f"Received multimodal vision response: {content[:100]}...")
            return content.strip()
    except Exception as exc:
        logger.warning(f"Multimodal vision inference call failed or endpoint not supported: {exc}")

    return None


def normalize_ocr_spacing_and_artifacts(text: str) -> str:
    """Generically cleans OCR spacing artifacts, concatenated words, and punctuation boundaries."""
    if not text:
        return ""

    s = text.strip()

    # 1. Add space after punctuation if missing space before a word (e.g. "complaints!C" -> "complaints! C")
    s = re.sub(r"([.,!?:;])([A-Za-z])", r"\1 \2", s)

    # 2. Add space between lower-case and upper-case transition (e.g. "OFAN ERA" -> "OF AN ERA", "eraThe" -> "era The")
    s = re.sub(r"([a-z])([A-Z])", r"\1 \2", s)

    # 3. Add space between letters and long digit sequences (e.g. "UPSCALERTS347" -> "UPSCALERTS 347")
    s = re.sub(r"([a-zA-Z])(\d{3,})", r"\1 \2", s)

    # 4. Common concatenated verb/preposition OCR joins (e.g. "isreportedlyset" -> "is reportedly set")
    s = re.sub(r"\b(is|are|was|were|will|has|have|had|be|been)(reportedly|allegedly|currently|officially|announced|set|banned|closed|cured|demolished)", r"\1 \2", s, flags=re.IGNORECASE)
    s = re.sub(r"(reportedly|allegedly|currently|officially|announced)(set|banned|closed|cured|demolished)", r"\1 \2", s, flags=re.IGNORECASE)
    s = re.sub(r"([a-z]{2,})(new|subsidy|for|after|before)\b", r"\1 \2", s, flags=re.IGNORECASE)

    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


STOPWORDS = {
    "the", "a", "an", "in", "on", "at", "of", "to", "for", "with", "by", "and", "or", "but",
    "is", "are", "was", "were", "be", "been", "being", "it", "its", "this", "that", "these", "those",
    "they", "them", "their", "he", "him", "his", "she", "her", "we", "us", "our", "you", "your",
    "from", "as", "into", "through", "during", "before", "after", "above", "below", "between"
}


def is_plausible_factual_proposition(prop: str) -> bool:
    """Generically validates whether an extracted string represents a plausible factual proposition.

    Rejects:
    - Fragments with duplicate adjacent function words (e.g., 'The the', 'in in')
    - Fragments starting with a lowercase verb/preposition without preceding subject context
    - Fragments dominated by stopwords / function words (< 2 content words)
    - Fragments lacking a plausible subject/entity and predicate structure
    - Too-short or word-order corrupted fragments
    """
    if not prop or not prop.strip():
        return False

    clean_prop = prop.strip()
    words = clean_prop.split()

    # 1. Minimum total word count
    if len(words) < 3:
        return False

    # 2. Reject duplicate adjacent function words/stopwords (e.g. "The the", "in in", "of of")
    for i in range(len(words) - 1):
        w1 = re.sub(r"[^\w]", "", words[i].lower())
        w2 = re.sub(r"[^\w]", "", words[i + 1].lower())
        if w1 and w1 == w2 and w1 in STOPWORDS:
            return False

    # 3. Reject fragments starting with a lowercase word when subsequent words contain capitalized function words/nouns
    # e.g., "orbits The the" -> starts with lowercase "orbits" followed by uppercase "The"
    if words[0][0].islower() and any(w[0].isupper() for w in words[1:]):
        return False

    # 4. Count content words (words length >= 3 not in STOPWORDS)
    content_words = [re.sub(r"[^\w]", "", w) for w in words if len(re.sub(r"[^\w]", "", w)) >= 3 and re.sub(r"[^\w]", "", w).lower() not in STOPWORDS]

    # Must have at least 2 distinct content words (e.g. subject + predicate content)
    if len(content_words) < 2:
        return False

    # 5. Must have at least one alphabetic content word
    if not any(w.isalpha() and len(w) >= 3 for w in content_words):
        return False

    # 6. Reject fragments dominated by stopwords (stopword ratio >= 0.6 for short fragments <= 5 words)
    stopword_count = sum(1 for w in words if re.sub(r"[^\w]", "", w).lower() in STOPWORDS)
    if len(words) <= 5 and (stopword_count / len(words)) >= 0.6:
        return False

    return True


def extract_ocr_claim_proposition(raw_text: str) -> Optional[str]:
    """Generically extracts the core verifiable factual claim proposition from raw OCR text.

    - Cleans spacing artifacts and noise.
    - Strips leading all-caps headline/header tags (e.g. "END OF AN ERA", "BREAKING NEWS").
    - Strips trailing junk codes, handles, or metadata.
    - Generically validates that the proposition is a plausible factual proposition.
    - Faithful: Never adds external facts not present in OCR text.
    - Conservative: Returns None if no clear, reliable factual proposition is present.
    """
    if not raw_text or not raw_text.strip():
        return None

    cleaned = normalize_ocr_spacing_and_artifacts(raw_text)
    if not cleaned:
        return None

    # Step 1: Strip leading all-caps header/headline tags if remainder is a complete proposition
    # Example: "END OF AN ERA The Eiffel Tower is set..." -> "The Eiffel Tower is set..."
    header_pattern = r"^([A-Z0-9\s!:\-]{2,35})\s+([A-Z][a-z].*)$"
    m = re.match(header_pattern, cleaned)
    if m:
        header_tag = m.group(1).strip()
        body = m.group(2).strip()
        if len(body.split()) >= 3 and any(len(w) >= 2 and w.isalpha() for w in body.split()):
            cleaned = body

    # Step 2: Strip trailing noise/codes (e.g., "C UPSCALERTS 347", "@username", "http...", "Page 1")
    cleaned = re.sub(r"\s+(@[a-zA-Z0-9_]{3,20}|https?://\S+)\s*$", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"\s+[A-Z]?\s*[A-Z]{3,}\s*\d{1,5}\s*$", "", cleaned).strip()

    # Step 3: Evaluate candidate proposition(s)
    candidates = []
    if cleaned:
        candidates.append(cleaned)

    # Split into candidate sentences
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    for s in sentences:
        s_clean = s.strip()
        if s_clean and s_clean not in candidates:
            candidates.append(s_clean)

    # Filter candidates with generic structural validation
    valid_candidates = [c for c in candidates if is_plausible_factual_proposition(c)]

    if valid_candidates:
        # Select candidate with highest content word count
        best_proposition = max(valid_candidates, key=lambda c: len([w for w in c.split() if len(w) >= 3 and w.lower() not in STOPWORDS]))
        return best_proposition

    return None


def analyze_image(
    image_bytes: bytes,
    filename: Optional[str] = None,
    user_question: Optional[str] = None,
) -> AnalysisResult:
    """End-to-end multimodal verification pipeline for an uploaded image.

    1. Extracts visible text from image using OCR.
    2. Classifies question intent (fact check, visual question, text extraction, specific).
    3. Resolves claim proposition from actual image context rather than vague question strings.
    4. Routes to appropriate verification or image-understanding path.
    5. Returns grounded AnalysisResult with provenance and metadata.
    """
    start_time = time.time()
    logger.info(f"Beginning image analysis for file: {filename or 'unnamed_image'}")

    # Generate preview thumbnail for the UI
    preview_url = generate_thumbnail_data_url(image_bytes)

    # Step 1: Run OCR text extraction
    extracted_text, ocr_err = extract_text_from_image_bytes(image_bytes)
    has_ocr_text = bool(extracted_text and len(extracted_text.strip()) > 0)
    logger.info(f"OCR extracted text: '{extracted_text}' (error: {ocr_err})")

    clean_question = (user_question or "").strip()
    intent = classify_question_intent(clean_question)
    logger.info(f"Classified question intent: '{intent}' for user question: '{clean_question}'")

    # Step 2: Handle Visual Question Path
    if intent == "visual_question":
        vision_answer = analyze_with_multimodal_vision(image_bytes, clean_question)
        elapsed = round(time.time() - start_time, 2)
        if vision_answer:
            return AnalysisResult(
                claim=clean_question,
                claim_type=ClaimType.FACTUAL,
                verdict=AssessmentVerdict.SUPPORTED,
                verdict_symbol="🟢",
                verdict_title="VISUAL ANALYSIS",
                confidence_score=0.85,
                explanation=vision_answer,
                supporting_evidence=[],
                contradicting_evidence=[],
                evidence_limitations=["Visual assessment generated by multimodal image understanding."],
                all_sources=[],
                latency_seconds=elapsed,
                mode="image",
                user_question=clean_question,
                extracted_image_text=extracted_text or None,
                image_preview=preview_url,
                targeted_answer=vision_answer,
                resolved_claim=clean_question,
                question_intent="visual_question",
            )
        else:
            # Multimodal vision service unavailable / unconfigured
            return AnalysisResult(
                claim=clean_question,
                claim_type=ClaimType.FACTUAL,
                verdict=AssessmentVerdict.INSUFFICIENT_EVIDENCE,
                verdict_symbol="🟡",
                verdict_title="INSUFFICIENT EVIDENCE",
                confidence_score=0.3,
                explanation=(
                    f"Answering visual appearance or spatial questions ('{clean_question}') "
                    f"requires a configured multimodal vision service. Direct visual reasoning is currently "
                    f"unavailable or unconfigured for this environment."
                ),
                supporting_evidence=[],
                contradicting_evidence=[],
                evidence_limitations=["Multimodal visual reasoning service is not configured or available."],
                all_sources=[],
                latency_seconds=elapsed,
                mode="image",
                user_question=clean_question,
                extracted_image_text=extracted_text or None,
                image_preview=preview_url,
                targeted_answer=f"Visual question '{clean_question}' could not be evaluated because no active vision service is configured.",
                resolved_claim=clean_question,
                question_intent="visual_question",
            )

    # Step 3: Handle Text Extraction Path
    if intent == "text_extraction":
        elapsed = round(time.time() - start_time, 2)
        if has_ocr_text:
            return AnalysisResult(
                claim=extracted_text,
                claim_type=ClaimType.FACTUAL,
                verdict=AssessmentVerdict.SUPPORTED,
                verdict_symbol="🟢",
                verdict_title="TEXT EXTRACTED",
                confidence_score=0.95,
                explanation=f"Text successfully extracted from image: \"{extracted_text}\"",
                supporting_evidence=[],
                contradicting_evidence=[],
                evidence_limitations=[],
                all_sources=[],
                latency_seconds=elapsed,
                mode="image",
                user_question=clean_question or None,
                extracted_image_text=extracted_text,
                image_preview=preview_url,
                targeted_answer=extracted_text,
                resolved_claim=extracted_text,
                question_intent="text_extraction",
            )
        else:
            is_unavailable = bool(ocr_err and "unavailable" in ocr_err.lower())
            expl = ocr_err if is_unavailable else "No readable text could be extracted from the uploaded image."
            limit = [ocr_err] if is_unavailable else ["No OCR text detected in image payload."]
            return AnalysisResult(
                claim=filename or "Uploaded Image",
                claim_type=ClaimType.FACTUAL,
                verdict=AssessmentVerdict.INSUFFICIENT_EVIDENCE,
                verdict_symbol="🟡",
                verdict_title="INSUFFICIENT EVIDENCE",
                confidence_score=0.2,
                explanation=expl,
                supporting_evidence=[],
                contradicting_evidence=[],
                evidence_limitations=limit,
                all_sources=[],
                latency_seconds=elapsed,
                mode="image",
                user_question=clean_question or None,
                extracted_image_text=None,
                image_preview=preview_url,
                targeted_answer=expl,
                resolved_claim=None,
                question_intent="text_extraction",
            )

    # Step 4: Handle Verification & Specific Question Paths
    claim_to_verify = ""
    if intent == "fact_check_verify":
        if has_ocr_text:
            extracted_proposition = extract_ocr_claim_proposition(extracted_text)
            if extracted_proposition:
                claim_to_verify = extracted_proposition
            else:
                # OCR text exists, but no reliable factual claim proposition could be extracted
                elapsed = round(time.time() - start_time, 2)
                return AnalysisResult(
                    claim=filename or "Uploaded Image",
                    claim_type=ClaimType.FACTUAL,
                    verdict=AssessmentVerdict.INSUFFICIENT_EVIDENCE,
                    verdict_symbol="🟡",
                    verdict_title="INSUFFICIENT EVIDENCE",
                    confidence_score=0.2,
                    explanation=(
                        "Could not extract a reliable, verifiable factual claim proposition from the image text. "
                        "Please upload an image containing a clear factual statement or flyer."
                    ),
                    supporting_evidence=[],
                    contradicting_evidence=[],
                    evidence_limitations=["Unextractable OCR text payload."],
                    all_sources=[],
                    latency_seconds=elapsed,
                    mode="image",
                    user_question=clean_question or None,
                    extracted_image_text=extracted_text,
                    image_preview=preview_url,
                    targeted_answer="Could not extract a reliable factual claim proposition from the image.",
                    resolved_claim=None,
                    question_intent="fact_check_verify",
                )
        else:
            # Neither readable OCR text nor a specific claim proposition is available
            elapsed = round(time.time() - start_time, 2)
            return AnalysisResult(
                claim=filename or "Uploaded Image",
                claim_type=ClaimType.FACTUAL,
                verdict=AssessmentVerdict.INSUFFICIENT_EVIDENCE,
                verdict_symbol="🟡",
                verdict_title="INSUFFICIENT EVIDENCE",
                confidence_score=0.2,
                explanation=(
                    "No legible text or factual claim was detected in the uploaded image to verify, "
                    "and no specific claim topic was provided. Please upload an image containing "
                    "readable text (such as a news article, flyer, or document) or specify a factual claim."
                ),
                supporting_evidence=[],
                contradicting_evidence=[],
                evidence_limitations=["No OCR text or verifiable claim proposition detected in image payload."],
                all_sources=[],
                latency_seconds=elapsed,
                mode="image",
                user_question=clean_question or None,
                extracted_image_text=None,
                image_preview=preview_url,
                targeted_answer="No legible factual claim detected in image to verify.",
                resolved_claim=None,
                question_intent="fact_check_verify",
            )
    else:  # intent == "specific_question"
        if has_ocr_text:
            extracted_proposition = extract_ocr_claim_proposition(extracted_text)
            if extracted_proposition:
                claim_to_verify = extracted_proposition
            elif clean_question:
                claim_to_verify = clean_question
        elif clean_question:
            claim_to_verify = clean_question

    if not claim_to_verify:
        elapsed = round(time.time() - start_time, 2)
        return AnalysisResult(
            claim=filename or "Uploaded Image",
            claim_type=ClaimType.FACTUAL,
            verdict=AssessmentVerdict.INSUFFICIENT_EVIDENCE,
            verdict_symbol="🟡",
            verdict_title="INSUFFICIENT EVIDENCE",
            confidence_score=0.2,
            explanation="Could not resolve a verifiable claim proposition from the image and question.",
            supporting_evidence=[],
            contradicting_evidence=[],
            evidence_limitations=["Unresolvable image claim proposition."],
            all_sources=[],
            latency_seconds=elapsed,
            mode="image",
            user_question=clean_question or None,
            extracted_image_text=extracted_text or None,
            image_preview=preview_url,
            targeted_answer="Could not resolve claim from image context.",
            resolved_claim=None,
            question_intent=intent,
        )

    # Step 5: Run evidence-first verification pipeline on the resolved claim proposition
    logger.info(f"Resolved claim proposition for verification: '{claim_to_verify}'")
    analysis_res = analyze_claim_single(claim_to_verify)

    elapsed = round(time.time() - start_time, 2)

    # Step 6: Augment result with image metadata and resolution details
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
        resolved_claim=claim_to_verify,
        question_intent=intent,
    )
