"""Webpage fetching, HTTP response handling, and structured metadata extraction module."""

import logging
import re
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup

from .source_filter import extract_domain
from .extractor import clean_html_to_text, HEADERS

logger = logging.getLogger(__name__)


class WebpageFetchResult:
    """Data object storing extracted webpage metadata and cleaned main content."""

    def __init__(
        self,
        url: str,
        domain: str,
        status_code: int,
        title: Optional[str] = None,
        canonical_url: Optional[str] = None,
        publication_date: Optional[str] = None,
        author: Optional[str] = None,
        main_text: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        self.url = url
        self.domain = domain
        self.status_code = status_code
        self.title = title
        self.canonical_url = canonical_url
        self.publication_date = publication_date
        self.author = author
        self.main_text = main_text
        self.error_message = error_message

    @property
    def is_success(self) -> bool:
        return self.status_code == 200 and bool(self.main_text and self.main_text.strip())


def fetch_webpage_content(url: str, timeout: float = 6.0) -> WebpageFetchResult:
    """Fetches a public webpage and extracts structured metadata + main text.

    Strictly preserves metadata truthfulness: missing fields remain None.
    Does NOT authenticate, bypass paywalls, or fabricate content.
    """
    clean_url = url.strip()
    if not clean_url.startswith(("http://", "https://")):
        clean_url = "https://" + clean_url

    domain = extract_domain(clean_url)
    if not domain:
        return WebpageFetchResult(
            url=clean_url,
            domain="unknown",
            status_code=400,
            error_message="Invalid or unparseable URL string.",
        )

    try:
        with httpx.Client(headers=HEADERS, timeout=timeout, follow_redirects=True) as client:
            resp = client.get(clean_url)
            status_code = resp.status_code

            if status_code != 200:
                return WebpageFetchResult(
                    url=clean_url,
                    domain=domain,
                    status_code=status_code,
                    error_message=f"Webpage returned HTTP status code {status_code}.",
                )

            content_type = resp.headers.get("content-type", "").lower()
            if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
                return WebpageFetchResult(
                    url=clean_url,
                    domain=domain,
                    status_code=status_code,
                    error_message="Unsupported content type (only HTML pages are supported).",
                )

            html_text = resp.text
            soup = BeautifulSoup(html_text, "html.parser")

            # Extract Title
            title: Optional[str] = None
            og_title = soup.find("meta", property="og:title")
            if og_title and og_title.get("content"):
                title = str(og_title["content"]).strip()
            elif soup.title and soup.title.string:
                title = str(soup.title.string).strip()

            # Extract Canonical URL
            canonical_url: Optional[str] = None
            link_canonical = soup.find("link", rel="canonical")
            if link_canonical and link_canonical.get("href"):
                canonical_url = str(link_canonical["href"]).strip()

            # Extract Publication Date
            pub_date: Optional[str] = None
            for meta_name in ["article:published_time", "publication_date", "date", "dc.date"]:
                meta_tag = soup.find("meta", property=meta_name) or soup.find("meta", attrs={"name": meta_name})
                if meta_tag and meta_tag.get("content"):
                    pub_date = str(meta_tag["content"]).strip()
                    break
            if not pub_date:
                time_tag = soup.find("time")
                if time_tag and time_tag.get("datetime"):
                    pub_date = str(time_tag["datetime"]).strip()

            # Extract Author
            author: Optional[str] = None
            for meta_name in ["author", "article:author", "dc.creator"]:
                meta_tag = soup.find("meta", property=meta_name) or soup.find("meta", attrs={"name": meta_name})
                if meta_tag and meta_tag.get("content"):
                    author = str(meta_tag["content"]).strip()
                    break

            # Extract Main Text
            main_text = clean_html_to_text(html_text)

            return WebpageFetchResult(
                url=clean_url,
                domain=domain,
                status_code=200,
                title=title if title else None,
                canonical_url=canonical_url if canonical_url else None,
                publication_date=pub_date if pub_date else None,
                author=author if author else None,
                main_text=main_text if main_text else None,
            )

    except httpx.TimeoutException:
        logger.warning(f"Timeout fetching webpage: {clean_url}")
        return WebpageFetchResult(
            url=clean_url,
            domain=domain,
            status_code=408,
            error_message="Webpage fetch request timed out.",
        )
    except Exception as exc:
        logger.warning(f"Error fetching webpage {clean_url}: {exc}")
        return WebpageFetchResult(
            url=clean_url,
            domain=domain,
            status_code=500,
            error_message=f"Unable to access webpage: {str(exc)}",
        )
