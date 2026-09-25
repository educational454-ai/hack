"""URL normalization and equivalence comparison module for subject-page evidence isolation."""

import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

# Common tracking / analytics query parameters to strip during normalization
TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
    "spm",
}


def normalize_url(url: str) -> str:
    """Normalizes a URL string for exact subject-page equivalence comparison.
    
    Operations:
    1. Trims whitespace and ensures http/https scheme.
    2. Lowercases scheme and hostname.
    3. Removes default ports (:80, :443).
    4. Strips URL fragments (#...).
    5. Strips common tracking query parameters (utm_source, fbclid, etc.).
    6. Sorts remaining query parameters.
    7. Normalizes trailing slashes (strips trailing slash except for root path '/').
    """
    if not url or not isinstance(url, str):
        return ""

    clean = url.strip()
    if not clean:
        return ""

    clean_lower = clean.lower()
    if not clean_lower.startswith(("http://", "https://")):
        clean = "https://" + clean

    try:
        parsed = urlparse(clean)

        scheme = "https" if parsed.scheme.lower() in ("http", "https") else parsed.scheme.lower()
        netloc = parsed.netloc.lower().split(":")[0]  # Remove port

        # Normalize path: strip trailing slash unless root path
        path = parsed.path
        if path and path != "/" and path.endswith("/"):
            path = path.rstrip("/")

        # Strip tracking query parameters
        query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
        filtered_query = [
            (k, v) for k, v in query_pairs if k.lower() not in TRACKING_PARAMS
        ]
        filtered_query.sort(key=lambda pair: pair[0])
        query_str = urlencode(filtered_query) if filtered_query else ""

        # Ignore fragments
        fragment_str = ""

        normalized = urlunparse((scheme, netloc, path, parsed.params, query_str, fragment_str))
        return normalized

    except Exception:
        return clean.lower().rstrip("/")


def are_urls_equivalent(url_a: str, url_b: str) -> bool:
    """Checks whether two URLs point to the exact same subject webpage after normalization."""
    if not url_a or not url_b:
        return False

    norm_a = normalize_url(url_a)
    norm_b = normalize_url(url_b)

    if not norm_a or not norm_b:
        return False

    return norm_a == norm_b
