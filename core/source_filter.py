"""Source filtering and tier categorization module.

Categorizes evidence sources into:
- PRIMARY: Government, academic research, legal registries, official bodies.
- SECONDARY: Established news agencies, wire services, recognized fact-checkers.
- LOW_CONFIDENCE: Social networks, user-generated forums, unverified personal blogs.
"""

from urllib.parse import urlparse
from typing import Tuple
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
    """Extracts the clean root domain from a URL."""
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return url.lower()


def classify_source(url: str, title: str = "") -> Tuple[SourceTier, str, float]:
    """Classifies a URL into a SourceTier with an authority score and explanation.

    Returns:
        (SourceTier, explanation, authority_weight)
    """
    domain = extract_domain(url)

    # 1. Check Primary indicators
    if domain in PRIMARY_DOMAINS or any(domain.endswith(tld) for tld in PRIMARY_TLDS):
        return (
            SourceTier.PRIMARY,
            "Primary source: Official government authority, academic publication, or recognized legal repository.",
            1.0,
        )

    # 2. Check Low-Confidence indicators
    if any(low in domain for low in LOW_CONFIDENCE_DOMAINS):
        return (
            SourceTier.LOW_CONFIDENCE,
            "Low-confidence source: User-generated content platform, forum, or unvetted blog.",
            0.4,
        )

    # 3. Check Secondary indicators
    if any(sec in domain for sec in SECONDARY_DOMAINS):
        return (
            SourceTier.SECONDARY,
            "Secondary source: Established journalistic outlet, news agency, or recognized fact-checking organization.",
            0.85,
        )

    # 4. Fallback: Check if it's a general .org or news site
    if domain.endswith(".org"):
        return (
            SourceTier.SECONDARY,
            "Secondary source: Institutional or non-profit organization domain.",
            0.75,
        )

    # Default general web source
    return (
        SourceTier.SECONDARY,
        "Secondary source: General web publication or news portal.",
        0.70,
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
