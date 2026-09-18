"""Evidence Quality Gate module.

Evaluates ranked candidate evidence items after semantic ranking and before
LLM verification to filter out invalid, empty, duplicate, or insufficient quality sources.
"""

import logging
import re
from typing import List, Tuple, Dict, Any, Optional
from urllib.parse import urlparse
from .config import config
from .schemas import EvidenceItem, SourceTier

logger = logging.getLogger(__name__)

# Default quality gate threshold constants
DEFAULT_MIN_PASSAGE_WORDS = 10
DEFAULT_MIN_RELEVANCE_PRIMARY = 0.15
DEFAULT_MIN_RELEVANCE_SECONDARY = 0.25
DEFAULT_MIN_RELEVANCE_LOW_CONFIDENCE = 0.45


def is_valid_url(url: Optional[str]) -> bool:
    """Validates that a URL is a non-empty string with valid netloc/hostname."""
    if not url or not isinstance(url, str):
        return False
    url_str = url.strip()
    if not url_str:
        return False
    try:
        if not url_str.startswith(("http://", "https://", "ftp://")):
            url_str = "http://" + url_str
        parsed = urlparse(url_str)
        netloc = (parsed.netloc or "").strip()
        return bool(netloc and ("." in netloc or netloc == "localhost"))
    except Exception:
        return False


def _normalize_text_for_dedup(text: str) -> str:
    """Normalizes passage text for duplicate detection."""
    if not text:
        return ""
    return re.sub(r"\W+", "", text.lower())


def filter_evidence_for_verification(
    evidence_items: List[EvidenceItem],
    min_passage_words: int = DEFAULT_MIN_PASSAGE_WORDS,
    min_rel_primary: float = DEFAULT_MIN_RELEVANCE_PRIMARY,
    min_rel_secondary: float = DEFAULT_MIN_RELEVANCE_SECONDARY,
    min_rel_low_conf: float = DEFAULT_MIN_RELEVANCE_LOW_CONFIDENCE,
) -> Tuple[List[EvidenceItem], List[Dict[str, Any]]]:
    """Filters candidate evidence items through conservative quality gate criteria.

    Evaluates:
    - URL validity
    - Extracted passage word count / text presence
    - Duplicate detection (by URL or identical passage text)
    - Source tier-dependent relevance thresholds

    Returns:
        (usable_evidence, rejected_evidence)
        where usable_evidence is the list of passed EvidenceItem instances,
        and rejected_evidence is a list of dicts describing rejection details.
    """
    if not evidence_items:
        return [], []

    usable_evidence: List[EvidenceItem] = []
    rejected_evidence: List[Dict[str, Any]] = []
    seen_passages = set()

    for item in evidence_items:
        # 1. URL Validity Check
        if not is_valid_url(item.url):
            rejected_evidence.append({
                "item": item,
                "reason": "invalid_url",
                "details": "Evidence item URL is missing, invalid, or malformed.",
            })
            continue

        # 2. Text / Snippet Availability Check
        passage_text = (item.passage or "").strip()
        words = passage_text.split()
        if len(words) < min_passage_words:
            rejected_evidence.append({
                "item": item,
                "reason": "empty_content",
                "details": f"Evidence passage has insufficient text ({len(words)} words < {min_passage_words}).",
            })
            continue

        # 3. Duplicate Detection Check (by passage text)
        norm_passage = _normalize_text_for_dedup(passage_text)
        if norm_passage and norm_passage in seen_passages:
            rejected_evidence.append({
                "item": item,
                "reason": "duplicate_content",
                "details": "Evidence item is a duplicate of a higher-ranked item.",
            })
            continue

        # 4. Tier-Dependent Quality & Relevance Check
        tier = item.source_tier
        score = item.similarity_score

        if tier == SourceTier.PRIMARY:
            threshold = min_rel_primary
        elif tier == SourceTier.SECONDARY:
            threshold = min_rel_secondary
        else:  # SourceTier.LOW_CONFIDENCE
            threshold = min_rel_low_conf

        if score < threshold:
            reason_code = (
                "low_confidence_quality_bar"
                if tier == SourceTier.LOW_CONFIDENCE
                else "insufficient_relevance"
            )
            rejected_evidence.append({
                "item": item,
                "reason": reason_code,
                "details": (
                    f"Similarity score {score:.4f} is below threshold {threshold:.2f} "
                    f"for {tier.value.upper()} source quality tier."
                ),
            })
            continue

        # Passed all checks
        if norm_passage:
            seen_passages.add(norm_passage)
        usable_evidence.append(item)

    logger.info(
        f"Evidence Quality Gate: {len(usable_evidence)} accepted, "
        f"{len(rejected_evidence)} rejected out of {len(evidence_items)} candidates."
    )
    return usable_evidence, rejected_evidence
