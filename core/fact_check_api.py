"""Google Fact Check Tools API integration.

Queries the Google Fact Check Tools API (v1alpha1) to retrieve published
fact-checks from 100+ organisations (Snopes, AFP, PolitiFact, Reuters, etc.)
that directly match the input claim.

Docs: https://developers.google.com/fact-check/tools/api/reference/rest/v1alpha1/claims/search
API key: free, 1 000 req/day — https://console.cloud.google.com/apis/library/factchecktools.googleapis.com

The results are treated as PRIMARY-tier evidence and injected early into the
verification pipeline so the LLM and heuristic verifier can leverage them.
"""

import logging
import re
from typing import List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

_FACT_CHECK_ENDPOINT = (
    "https://factchecktools.googleapis.com/v1alpha1/claims:search"
)

# Maps textual ratings from various publishers → a normalised verdict signal
# used to bias the pipeline verdict when authoritative fact-checks are found.
_RATING_TO_SIGNAL = {
    # Strong FALSE signals
    "false": "contradicted",
    "mostly false": "contradicted",
    "pants on fire": "contradicted",
    "fake": "contradicted",
    "incorrect": "contradicted",
    "inaccurate": "contradicted",
    "fabricated": "contradicted",
    "misleading": "contradicted",
    "misinformation": "contradicted",
    "not true": "contradicted",
    "wrong": "contradicted",
    "debunked": "contradicted",
    "fiction": "contradicted",
    "no evidence": "contradicted",
    # Strong TRUE signals
    "true": "supported",
    "mostly true": "supported",
    "correct": "supported",
    "accurate": "supported",
    "verified": "supported",
    "confirmed": "supported",
    # Ambiguous / partial
    "half true": "conflicting",
    "mixed": "conflicting",
    "partially true": "conflicting",
    "partly false": "conflicting",
    "disputed": "conflicting",
    "unverified": "insufficient_evidence",
    "unproven": "insufficient_evidence",
    "needs context": "insufficient_evidence",
}


def _normalise_rating(rating: str) -> str:
    """Returns the normalised verdict signal for a raw publisher rating string."""
    cleaned = rating.strip().lower()
    # Direct lookup
    if cleaned in _RATING_TO_SIGNAL:
        return _RATING_TO_SIGNAL[cleaned]
    # Partial match — iterate longest-match first
    for key in sorted(_RATING_TO_SIGNAL, key=len, reverse=True):
        if key in cleaned:
            return _RATING_TO_SIGNAL[key]
    return "insufficient_evidence"


def search_fact_checks(
    claim: str,
    api_key: str,
    language_code: str = "en",
    max_results: int = 5,
) -> List[dict]:
    """Queries Google Fact Check Tools API and returns structured fact-check items.

    Args:
        claim: The claim text to look up.
        api_key: Google Cloud API key with Fact Check Tools API enabled.
        language_code: BCP-47 language code (default 'en').
        max_results: Maximum number of fact-check results to return.

    Returns:
        List of dicts with keys:
          claim_text, claimant, claim_date, rating, rating_url,
          publisher_name, publisher_site, title, verdict_signal
    """
    if not claim or not claim.strip():
        return []
    if not api_key or len(api_key) < 10:
        logger.debug("Google Fact Check API key not configured — skipping.")
        return []

    params = {
        "query": claim.strip(),
        "key": api_key,
        "languageCode": language_code,
        "pageSize": max_results,
    }

    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(_FACT_CHECK_ENDPOINT, params=params)

        if resp.status_code != 200:
            logger.warning(
                f"[FactCheckAPI] HTTP {resp.status_code}: {resp.text[:200]}"
            )
            return []

        data = resp.json()
    except Exception as exc:
        logger.warning(f"[FactCheckAPI] Request failed: {exc}")
        return []

    results = []
    for claim_obj in data.get("claims", []):
        claim_text = claim_obj.get("text", "").strip()
        claimant = claim_obj.get("claimant", "").strip() or None
        claim_date = claim_obj.get("claimDate", "").strip() or None

        for review in claim_obj.get("claimReview", []):
            publisher = review.get("publisher", {})
            publisher_name = publisher.get("name", "").strip() or "Unknown Publisher"
            publisher_site = publisher.get("site", "").strip() or ""

            title = review.get("title", "").strip() or claim_text
            rating_raw = review.get("textualRating", "").strip()
            rating_url = review.get("url", "").strip()

            if not rating_raw or not rating_url:
                continue  # Skip entries without a clear rating or link

            verdict_signal = _normalise_rating(rating_raw)

            results.append(
                {
                    "claim_text": claim_text,
                    "claimant": claimant,
                    "claim_date": claim_date,
                    "rating": rating_raw,
                    "rating_url": rating_url,
                    "publisher_name": publisher_name,
                    "publisher_site": publisher_site,
                    "title": title,
                    "verdict_signal": verdict_signal,
                }
            )
            if len(results) >= max_results:
                break

        if len(results) >= max_results:
            break

    logger.info(
        f"[FactCheckAPI] Found {len(results)} fact-check(s) for claim: "
        f"'{claim[:80]}'"
    )
    return results


def fact_checks_to_evidence_items(
    fact_checks: List[dict],
) -> List[dict]:
    """Converts raw fact-check API results into evidence-item dicts compatible
    with the existing pipeline schema (same shape as extractor output).

    These items are tagged as PRIMARY source tier since they come from
    professional fact-checking organisations.
    """
    evidence_items = []
    for idx, fc in enumerate(fact_checks):
        publisher = fc.get("publisher_name", "Fact-Check Publisher")
        site = fc.get("publisher_site", "factcheck.org")
        rating = fc.get("rating", "")
        claim_text = fc.get("claim_text", "")
        title = fc.get("title", "")
        url = fc.get("rating_url", "")
        claimant = fc.get("claimant")
        claim_date = fc.get("claim_date")

        # Build a rich passage the LLM can reason over
        claimant_str = f" (claimed by {claimant})" if claimant else ""
        date_str = f" on {claim_date[:10]}" if claim_date else ""
        passage = (
            f'{publisher} rated the claim "{claim_text}"{claimant_str}{date_str} '
            f'as "{rating}". '
            f"Source: {title}"
        )

        evidence_items.append(
            {
                "url": url,
                "title": title or f"Fact-check by {publisher}",
                "domain": site or publisher.lower().replace(" ", "") + ".com",
                "source_tier": "primary",   # Fact-checkers = PRIMARY tier
                "passage": passage,
                "_fact_check_meta": fc,     # Carry full metadata for schema
            }
        )
    return evidence_items


def aggregate_fact_check_verdict(fact_checks: List[dict]) -> Optional[Tuple[str, float]]:
    """Derives an aggregate verdict signal + confidence from multiple fact-checks.

    Returns (verdict_signal, confidence) or None if no conclusive signal.
    """
    if not fact_checks:
        return None

    signal_counts: dict = {}
    for fc in fact_checks:
        sig = fc.get("verdict_signal", "insufficient_evidence")
        signal_counts[sig] = signal_counts.get(sig, 0) + 1

    total = sum(signal_counts.values())

    # Determine dominant signal
    dominant = max(signal_counts, key=lambda k: signal_counts[k])
    dominant_count = signal_counts[dominant]
    ratio = dominant_count / total

    if dominant == "insufficient_evidence" or ratio < 0.5:
        return None  # No clear signal

    # Confidence scales with agreement ratio and total count
    # More publishers agreeing → higher confidence (max 0.97)
    base_conf = 0.80 + min(0.17, 0.05 * dominant_count)
    conf = round(min(0.97, base_conf * ratio), 3)

    return dominant, conf
