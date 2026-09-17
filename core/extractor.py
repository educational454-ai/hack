"""Web page fetching, HTML cleaning, and passage extraction module."""

import logging
import re
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup
from .source_filter import classify_source, extract_domain

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

DISCARD_PATTERNS = [
    r"cookie policy",
    r"all rights reserved",
    r"subscribe to our newsletter",
    r"terms of use",
    r"privacy policy",
    r"sign in to continue",
]


def clean_html_to_text(html: str) -> str:
    """Strips boilerplate tags and extracts readable article text."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "header", "footer", "aside", "noscript", "form", "svg"]):
        tag.decompose()

    # Extract text from paragraphs, headers, and list items
    blocks = []
    for element in soup.find_all(["p", "h1", "h2", "h3", "article", "blockquote"]):
        text = element.get_text(separator=" ", strip=True)
        if len(text.split()) >= 6: # Ignore tiny snippets
            blocks.append(text)

    full_text = "\n\n".join(blocks)
    # Normalize whitespaces
    full_text = re.sub(r"[ \t]+", " ", full_text)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    return full_text.strip()


def chunk_text_into_passages(text: str, chunk_size_words: int = 180, overlap_words: int = 25) -> List[str]:
    """Splits continuous text into coherent passage chunks with small overlap."""
    words = text.split()
    if len(words) <= chunk_size_words:
        return [text] if len(words) >= 15 else []

    passages = []
    step = chunk_size_words - overlap_words
    for i in range(0, len(words), step):
        chunk_words = words[i : i + chunk_size_words]
        chunk = " ".join(chunk_words)

        # Check if chunk contains mostly boilerplate
        lower_chunk = chunk.lower()
        if any(re.search(bp, lower_chunk) for bp in DISCARD_PATTERNS):
            continue

        if len(chunk_words) >= 20:
            passages.append(chunk)

    return passages


from concurrent.futures import ThreadPoolExecutor, as_completed

def _fetch_single_candidate(item: Dict[str, Any], timeout: float) -> List[Dict[str, Any]]:
    """Fetches and extracts passages for a single search hit."""
    url = item.get("url", "")
    title = item.get("title", "")
    snippet = item.get("body", "")
    tier, _, _ = classify_source(url, title)
    domain = extract_domain(url)

    passages: List[str] = []

    try:
        with httpx.Client(headers=HEADERS, timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url)
            if resp.status_code == 200 and "text/html" in resp.headers.get("content-type", ""):
                page_text = clean_html_to_text(resp.text)
                passages = chunk_text_into_passages(page_text)
    except Exception as e:
        logger.debug(f"Could not fetch full page {url}: {e}")

    # Fallback to search snippet if full page had no passages or timed out
    if not passages and snippet and len(snippet.split()) >= 8:
        passages = [snippet]

    items = []
    for p in passages:
        items.append({
            "url": url,
            "title": title,
            "domain": domain,
            "source_tier": tier,
            "passage": p,
        })
    return items


def extract_evidence_from_candidates(candidates: List[Dict[str, Any]], timeout: float = 5.0) -> List[Dict[str, Any]]:
    """Extracts candidate passages concurrently from a list of search hits.
    
    Returns a list of extracted evidence dictionaries:
    [{'url': ..., 'title': ..., 'domain': ..., 'source_tier': ..., 'passage': ...}]
    """
    extracted_items: List[Dict[str, Any]] = []
    if not candidates:
        return []

    # Parallelize web page fetching across up to 8 threads
    max_workers = min(len(candidates), 8)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_candidate = {
            executor.submit(_fetch_single_candidate, item, timeout): item
            for item in candidates
        }
        for future in as_completed(future_to_candidate):
            try:
                items = future.result()
                extracted_items.extend(items)
            except Exception as e:
                logger.debug(f"Error extracting candidate: {e}")

    return extracted_items
