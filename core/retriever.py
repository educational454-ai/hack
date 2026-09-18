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
            # pyrefly: ignore [missing-import]
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

    # If no search candidates retrieved, return empty candidate list
    if not candidate_results:
        logger.info("No candidate search results obtained from web search.")
        return []

    return candidate_results


def retrieve_relevant_images(query: str, max_images: int = 4) -> List[Dict[str, Any]]:
    """Retrieves high-relevance news/topic images using DDGS."""
    images: List[Dict[str, Any]] = []
    try:
        from ddgs import DDGS
        ddgs_client = DDGS()
    except Exception:
        try:
            # pyrefly: ignore [missing-import]
            from duckduckgo_search import DDGS
            ddgs_client = DDGS()
        except Exception:
            ddgs_client = None

    if ddgs_client:
        try:
            results = list(ddgs_client.images(query, max_results=max_images))
            for item in results:
                if not isinstance(item, dict):
                    continue
                img_url = item.get("image") or item.get("image_url")
                if img_url:
                    title_val = item.get("title")
                    source_val = item.get("url") or item.get("source")
                    thumb_val = item.get("thumbnail") or img_url
                    images.append({
                        "title": str(title_val).strip() if title_val else None,
                        "image_url": str(img_url),
                        "thumbnail_url": str(thumb_val) if thumb_val else None,
                        "source_url": str(source_val).strip() if source_val else None,
                    })
        except Exception as e:
            logger.warning(f"Failed to retrieve images for '{query}': {e}")
    return images


def _generate_fallback_candidates(claim: str) -> List[Dict[str, Any]]:
    """Returns an empty candidate list when web search yields no candidates.
    
    Prevents synthetic or hardcoded evidence passages from entering the verification pipeline.
    """
    return []
