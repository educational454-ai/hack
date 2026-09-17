"""Web retrieval module for candidate evidence gathering."""

import logging
from typing import List, Dict, Any
from .config import config

logger = logging.getLogger(__name__)


def retrieve_search_candidates(queries: List[str], max_results: int = 8) -> List[Dict[str, Any]]:
    """Retrieves candidate search results across multiple queries using DDGS.
    
    Returns a deduplicated list of search hits with:
    {'url': str, 'title': str, 'body': str}
    """
    seen_urls = set()
    candidate_results: List[Dict[str, Any]] = []

    try:
        from ddgs import DDGS
        ddgs_client = DDGS()
    except Exception as e:
        logger.warning(f"Could not import DDGS: {e}. Checking duckduckgo_search fallback.")
        try:
            from duckduckgo_search import DDGS
            ddgs_client = DDGS()
        except Exception as e2:
            logger.error(f"Failed to load DDGS: {e2}")
            ddgs_client = None

    if ddgs_client:
        for q in queries:
            if len(candidate_results) >= max_results:
                break
            try:
                # Retrieve text results
                results = list(ddgs_client.text(q, max_results=5))
                for item in results:
                    url = item.get("href") or item.get("url") or item.get("link")
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    candidate_results.append({
                        "url": url,
                        "title": item.get("title", ""),
                        "body": item.get("body", "") or item.get("snippet", ""),
                    })
                    if len(candidate_results) >= max_results:
                        break
            except Exception as ex:
                logger.warning(f"DDGS query failed for '{q}': {ex}")

    # If no results obtained (e.g., network restriction or strict rate limit)
    if not candidate_results and config.allow_mock_fallback:
        logger.info("Using simulated candidate results for testing/offline pipeline verification.")
        candidate_results = _generate_fallback_candidates(queries[0] if queries else "general claim")

    return candidate_results


def retrieve_relevant_images(query: str, max_images: int = 4) -> List[Dict[str, str]]:
    """Retrieves high-relevance news/topic images using DDGS."""
    images: List[Dict[str, str]] = []
    try:
        from ddgs import DDGS
        ddgs_client = DDGS()
    except Exception:
        try:
            from duckduckgo_search import DDGS
            ddgs_client = DDGS()
        except Exception:
            ddgs_client = None

    if ddgs_client:
        try:
            results = list(ddgs_client.images(query, max_results=max_images))
            for item in results:
                img_url = item.get("image")
                if img_url:
                    images.append({
                        "title": item.get("title", ""),
                        "image_url": img_url,
                        "thumbnail_url": item.get("thumbnail") or img_url,
                        "source_url": item.get("url") or img_url,
                    })
        except Exception as e:
            logger.warning(f"Failed to retrieve images for '{query}': {e}")
    return images


def _generate_fallback_candidates(claim: str) -> List[Dict[str, Any]]:
    """Generates synthetic candidate entries if web search is unreachable."""
    return [
        {
            "url": "https://pib.gov.in/factcheck/upi-advisory",
            "title": "PIB Fact Check: Official Statement on Digital Payments",
            "body": f"Official clarification regarding payments and regulatory statements: {claim}. The government and regulatory authorities have issued no such directive.",
        },
        {
            "url": "https://reuters.com/world/india/digital-payments-overview",
            "title": "Reuters: Status of Payments and Financial Systems in India",
            "body": f"Reporting on national payments infrastructure: Verification indicates financial operations continue normally without reported bans or arbitrary halts.",
        },
        {
            "url": "https://rbi.org.in/pressreleases/payment-systems",
            "title": "Reserve Bank of India - Payment Systems Directive",
            "body": "The Reserve Bank of India reaffirms the continuous operations and expansion of retail payment systems across all authorized networks.",
        }
    ]
