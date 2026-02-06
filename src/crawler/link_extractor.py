"""
Link Extractor (Requirement #2)
===============================
Discovers, normalizes, and filters URLs from HTML pages.
"""

import logging
import re
from typing import List, Set, Optional
from urllib.parse import urljoin, urlparse, urlunparse

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class LinkExtractor:
    """Extracts and filters links from HTML pages."""

    def __init__(
        self,
        allowed_domains: Optional[Set[str]] = None,
        same_domain_only: bool = True,
        excluded_patterns: Optional[List[str]] = None,
        strip_fragments: bool = True,
    ):
        self.allowed_domains = allowed_domains or set()
        self.same_domain_only = same_domain_only
        self.excluded_patterns = excluded_patterns or []
        self.strip_fragments = strip_fragments
        self._compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in self.excluded_patterns
        ]

    def extract_links(self, html: str, base_url: str) -> List[str]:
        """Extract all valid links from HTML page."""
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        base_domain = urlparse(base_url).netloc
        seen: Set[str] = set()
        links: List[str] = []

        for tag in soup.find_all("a", href=True):
            href = tag["href"].strip()

            if not href or href.startswith(("javascript:", "mailto:", "tel:", "#")):
                continue

            absolute_url = urljoin(base_url, href)
            normalized = self._normalize_url(absolute_url)
            if not normalized:
                continue

            parsed = urlparse(normalized)
            if parsed.scheme not in ("http", "https"):
                continue

            if not self._is_domain_allowed(parsed.netloc, base_domain):
                continue

            if self._is_excluded(normalized):
                continue

            if normalized not in seen:
                seen.add(normalized)
                links.append(normalized)

        return links

    def _normalize_url(self, url: str) -> Optional[str]:
        try:
            parsed = urlparse(url)
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            path = parsed.path
            if path != "/" and path.endswith("/"):
                path = path.rstrip("/")
            fragment = "" if self.strip_fragments else parsed.fragment
            return urlunparse((scheme, netloc, path, parsed.params, parsed.query, fragment))
        except Exception:
            return None

    def _is_domain_allowed(self, domain: str, base_domain: str) -> bool:
        if self.allowed_domains:
            return domain in self.allowed_domains
        if self.same_domain_only:
            return domain == base_domain
        return True

    def _is_excluded(self, url: str) -> bool:
        for pattern in self._compiled_patterns:
            if pattern.search(url):
                return True
        return False

    @staticmethod
    def get_domain(url: str) -> str:
        return urlparse(url).netloc