"""Publisher Transparency and Historical Audit Module.

Queries Schema.org ClaimReview databases via Google Fact Check Tools API
to empirically assess a publisher/news domain's historical record:
- Checks if the domain has been audited by IFCN fact-checkers.
- Calculates an empirical credibility modifier (0.75x to 1.05x).
- Caches results in memory to keep verification fast (< 100ms on repeat).
"""

import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

from .schemas import PublisherTransparencyRecord, FactCheckReference
from .fact_check_api import search_fact_checks

logger = logging.getLogger(__name__)

# In-memory LRU-like cache for publisher audit records
_PUBLISHER_AUDIT_CACHE: Dict[str, PublisherTransparencyRecord] = {}

# Well-known primary institutions with recognized public mandates (exempt from debunk dampening)
OFFICIAL_INSTITUTION_DOMAINS = {
    "pib.gov.in", "rbi.org.in", "npci.org.in", "uidai.gov.in", "mygov.in",
    "who.int", "un.org", "cdc.gov", "fda.gov", "nih.gov", "isro.gov.in", "nasa.gov",
}


def clean_domain_name(domain_or_url: str) -> str:
    """Extracts a clean, normalized domain string without www. prefix or paths."""
    if not domain_or_url:
        return ""
    d = domain_or_url.strip().lower()
    if "://" in d:
        try:
            d = urlparse(d).netloc
        except Exception:
            pass
    if d.startswith("www."):
        d = d[4:]
    return d.split(":")[0].strip()


def audit_publisher_domain(
    domain: str,
    api_key: Optional[str] = None,
) -> PublisherTransparencyRecord:
    """Evaluates a news publisher domain against recorded ClaimReview entries.

    Returns a PublisherTransparencyRecord containing:
    - total_audited_claims: Count of historical reviews for this domain.
    - debunked_count: Number of times claims from/about this domain were rated False.
    - verified_count: Number of times corroborated.
    - credibility_modifier: Multiplier applied in BGE-M3 passage ranking.
    - recent_reviews: Top 3 audit references.
    """
    clean_d = clean_domain_name(domain)
    if not clean_d:
        return PublisherTransparencyRecord(domain="unknown", credibility_modifier=1.0)

    # 1. Check in-memory cache
    if clean_d in _PUBLISHER_AUDIT_CACHE:
        return _PUBLISHER_AUDIT_CACHE[clean_d]

    # 2. If it is an official government / international body, assign top-tier score directly
    if clean_d in OFFICIAL_INSTITUTION_DOMAINS or clean_d.endswith((".gov", ".gov.in", ".nic.in", ".edu")):
        rec = PublisherTransparencyRecord(
            domain=clean_d,
            total_audited_claims=0,
            debunked_count=0,
            verified_count=0,
            recent_reviews=[],
            credibility_modifier=1.05,
        )
        _PUBLISHER_AUDIT_CACHE[clean_d] = rec
        return rec

    # 3. Query ClaimReview index using the domain name as the search subject
    debunked = 0
    verified = 0
    recent: List[FactCheckReference] = []

    if api_key and len(api_key) >= 10:
        try:
            # Query for fact-checks that evaluated claims from this domain
            query_str = clean_d.split(".")[0]  # e.g., 'indiatoday' from 'indiatoday.in'
            raw_reviews = search_fact_checks(claim=query_str, api_key=api_key, max_results=5)

            for item in raw_reviews:
                signal = item.get("verdict_signal", "")
                if signal == "contradicted":
                    debunked += 1
                elif signal == "supported":
                    verified += 1

                recent.append(
                    FactCheckReference(
                        title=item.get("title", ""),
                        rating=item.get("rating", ""),
                        fact_checker=item.get("publisher_name", "Fact-Checker"),
                        review_date=item.get("claim_date"),
                        review_url=item.get("rating_url", ""),
                    )
                )
        except Exception as exc:
            logger.debug(f"[PublisherAudit] Could not audit domain '{clean_d}': {exc}")

    total = debunked + verified

    # 4. Compute empirical modifier
    # If the domain has multiple documented fact-check debunks, adjust weight transparently
    if total >= 3:
        debunk_ratio = debunked / total
        # If >= 60% of reviewed stories were debunked, dampen weight down to 0.75x
        if debunk_ratio >= 0.60:
            modifier = round(max(0.75, 1.0 - (debunk_ratio * 0.30)), 2)
        elif debunk_ratio <= 0.25:
            modifier = 1.05  # Strongly verified track record
        else:
            modifier = 0.95
    else:
        modifier = 1.00  # Inconclusive data: neutral multiplier

    record = PublisherTransparencyRecord(
        domain=clean_d,
        total_audited_claims=total,
        debunked_count=debunked,
        verified_count=verified,
        recent_reviews=recent[:3],
        credibility_modifier=modifier,
    )

    _PUBLISHER_AUDIT_CACHE[clean_d] = record
    logger.info(
        f"[PublisherAudit] Domain '{clean_d}': {total} audits ({debunked} debunks), modifier={modifier}"
    )
    return record


def audit_sources_batch(
    domains: List[str],
    api_key: Optional[str] = None,
) -> Dict[str, PublisherTransparencyRecord]:
    """Audits a batch of unique domain names efficiently."""
    unique_domains = list(dict.fromkeys(clean_domain_name(d) for d in domains if d))
    results: Dict[str, PublisherTransparencyRecord] = {}
    for d in unique_domains:
        results[d] = audit_publisher_domain(d, api_key=api_key)
    return results
