"""Source filtering and tier categorization module.

Categorizes evidence sources into:
- PRIMARY: Government, academic research, legal registries, official bodies.
- SECONDARY: Established news agencies, wire services, recognized fact-checkers.
- LOW_CONFIDENCE: Social networks, user-generated forums, unverified personal blogs.
"""

from urllib.parse import urlparse
from typing import Tuple, Iterable
from .schemas import SourceTier, SourceMetadata

# High-authority official / primary domains & suffixes
PRIMARY_DOMAINS = {
    "pib.gov.in", "rbi.org.in", "npci.org.in", "uidai.gov.in", "mygov.in",
    "sci.gov.in", "who.int", "un.org", "cdc.gov", "fda.gov", "nih.gov",
    "arxiv.org", "nature.com", "thelancet.com", "sciencedirect.com",
    "springer.com", "biorxiv.org", "pubmed.ncbi.nlm.nih.gov", "ncbi.nlm.nih.gov",
    "isro.gov.in", "nasa.gov", "supremecourtofindia.nic.in"
}

PRIMARY_TLDS = (".gov", ".gov.in", ".nic.in", ".gov.uk", ".gov.au", ".edu", ".ac.in", ".ac.uk", ".mil")

# Established news wire services & reporting outlets
SECONDARY_DOMAINS = {
    "reuters.com", "apnews.com", "bbc.com", "bbc.co.uk", "thehindu.com",
    "indianexpress.com", "timesofindia.indiatimes.com", "ndtv.com",
    "hindustantimes.com", "bloomberg.com", "wsj.com", "ft.com",
    "theguardian.com", "aljazeera.com", "afp.com", "ani.in", "pti.in",
    "altnews.in", "boomlive.in", "snopes.com", "factcheck.org", "politifact.com",
    "cnbc.com", "forbes.com", "economictimes.indiatimes.com", "business-standard.com",
    "theprint.in", "thewire.in", "scroll.in", "livemint.com", "moneycontrol.com",
    "techcrunch.com", "theverge.com", "wired.com", "arstechnica.com",
    "nature.com/news", "sciencedaily.com"
}

# Low confidence, social platforms, and user-generated forums
LOW_CONFIDENCE_DOMAINS = {
    "reddit.com", "twitter.com", "x.com", "facebook.com", "instagram.com",
    "tiktok.com", "quora.com", "medium.com", "blogspot.com", "wordpress.com",
    "tumblr.com", "pinterest.com", "threads.net", "youtube.com"
}


def extract_domain(url: str) -> str:
    """Extracts the clean root domain or host from a URL safely."""
    if not url or not isinstance(url, str):
        return ""
    try:
        url_str = url.strip()
        if not url_str:
            return ""
        if not url_str.startswith(("http://", "https://", "ftp://")):
            url_str = "http://" + url_str
        parsed = urlparse(url_str)
        netloc = (parsed.netloc or "").lower().split(":")[0].strip()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


def _clean_ref_domain(ref: str) -> str:
    ref_str = ref.strip().lower()
    ref_host = ref_str.split("/")[0].split(":")[0]
    if ref_host.startswith("www."):
        ref_host = ref_host[4:]
    return ref_host


def is_in_domain_set(domain: str, domain_set: Iterable[str]) -> bool:
    """Checks whether domain matches an exact domain or legitimate subdomain in domain_set.

    Prevents unsafe substring matching (e.g. 'notreuters.com' matching 'reuters.com').
    """
    if not domain:
        return False
    cand = domain.lower()
    if cand.startswith("www."):
        cand = cand[4:]

    for ref in domain_set:
        ref_host = _clean_ref_domain(ref)
        if not ref_host:
            continue
        if cand == ref_host or cand.endswith("." + ref_host):
            return True
    return False


def classify_source(url: str, title: str = "") -> Tuple[SourceTier, str, float]:
    """Classifies a URL into a SourceTier with an authority score and explanation.

    Returns:
        (SourceTier, explanation, authority_weight)
    """
    domain = extract_domain(url)

    if not domain:
        return (
            SourceTier.LOW_CONFIDENCE,
            "Low-confidence source: Unknown or unclassified web publication.",
            0.4,
        )

    # 1. Check Primary indicators
    if is_in_domain_set(domain, PRIMARY_DOMAINS) or any(
        domain == tld[1:] or domain.endswith(tld) for tld in PRIMARY_TLDS
    ):
        return (
            SourceTier.PRIMARY,
            "Primary source: Official government authority, academic publication, or recognized legal repository.",
            1.0,
        )

    # 2. Check Low-Confidence indicators (explicitly listed low-confidence domains)
    if is_in_domain_set(domain, LOW_CONFIDENCE_DOMAINS):
        return (
            SourceTier.LOW_CONFIDENCE,
            "Low-confidence source: User-generated content platform, forum, or unvetted blog.",
            0.4,
        )

    # 3. Check Secondary indicators (explicitly listed recognized secondary domains)
    if is_in_domain_set(domain, SECONDARY_DOMAINS):
        return (
            SourceTier.SECONDARY,
            "Secondary source: Established journalistic outlet, news agency, or recognized fact-checking organization.",
            0.85,
        )

    # 4. Fallback for unclassified / unknown domains: treat conservatively as LOW_CONFIDENCE
    return (
        SourceTier.LOW_CONFIDENCE,
        "Low-confidence source: Unknown or unclassified web publication.",
        0.4,
    )


def build_source_metadata(url: str, title: str = "") -> SourceMetadata:
    """Constructs SourceMetadata model for a given URL and title."""
    tier, reason, _ = classify_source(url, title)
    domain = extract_domain(url)
    return SourceMetadata(
        url=url,
        domain=domain,
        title=title,
        tier=tier,
        tier_reason=reason,
    )
