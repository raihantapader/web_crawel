"""
Content Parser (Requirement #3)
===============================
Extracts structured content from HTML pages.
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from bs4 import BeautifulSoup, Comment

logger = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Base class for custom extractors."""
    
    @abstractmethod
    def extract(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        pass


class MetadataExtractor(BaseExtractor):
    """Extracts meta tags, Open Graph, Twitter Cards."""

    def extract(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        metadata = {}

        # Description
        desc = soup.find("meta", attrs={"name": "description"})
        if desc and desc.get("content"):
            metadata["description"] = desc["content"].strip()

        # Keywords
        kw = soup.find("meta", attrs={"name": "keywords"})
        if kw and kw.get("content"):
            metadata["keywords"] = [k.strip() for k in kw["content"].split(",")]

        # Open Graph
        og_tags = soup.find_all("meta", attrs={"property": re.compile(r"^og:")})
        if og_tags:
            metadata["open_graph"] = {}
            for tag in og_tags:
                prop = tag.get("property", "").replace("og:", "")
                content = tag.get("content", "")
                if prop and content:
                    metadata["open_graph"][prop] = content

        # Canonical URL
        canonical = soup.find("link", attrs={"rel": "canonical"})
        if canonical and canonical.get("href"):
            metadata["canonical_url"] = canonical["href"]

        # Language
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            metadata["language"] = html_tag["lang"]

        return metadata


class JsonLdExtractor(BaseExtractor):
    """Extracts JSON-LD structured data."""

    def extract(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        json_ld_data = []
        for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
            try:
                if script.string:
                    json_ld_data.append(json.loads(script.string))
            except json.JSONDecodeError:
                pass
        return {"json_ld": json_ld_data} if json_ld_data else {}


class HeadingsExtractor(BaseExtractor):
    """Extracts heading structure (H1-H6)."""

    def extract(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        headings = {}
        for level in range(1, 7):
            tag = f"h{level}"
            found = soup.find_all(tag)
            if found:
                headings[tag] = [h.get_text(strip=True) for h in found]
        return {"headings": headings} if headings else {}


class ContentParser:
    """Main parser that orchestrates content extraction."""

    STRIP_TAGS = ["script", "style", "noscript", "iframe", "nav", "footer", "header"]

    def __init__(self, extractors: Optional[List[BaseExtractor]] = None):
        self._extractors: List[BaseExtractor] = [
            MetadataExtractor(),
            JsonLdExtractor(),
            HeadingsExtractor(),
        ]
        if extractors:
            self._extractors.extend(extractors)

    def add_extractor(self, extractor: BaseExtractor):
        self._extractors.append(extractor)

    def parse(self, html: str, url: str) -> Dict[str, Any]:
        """Parse HTML and extract structured content."""
        if not html:
            return {"title": "", "text": "", "metadata": {}}

        soup = BeautifulSoup(html, "html.parser")
        title = self._extract_title(soup)
        text = self._extract_text(soup)

        metadata = {}
        for extractor in self._extractors:
            try:
                result = extractor.extract(soup, url)
                metadata.update(result)
            except Exception as e:
                logger.debug(f"{extractor.__class__.__name__} failed: {e}")

        return {"title": title, "text": text, "metadata": metadata}

    def _extract_title(self, soup: BeautifulSoup) -> str:
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        return ""

    def _extract_text(self, soup: BeautifulSoup) -> str:
        soup_copy = BeautifulSoup(str(soup), "html.parser")
        for tag_name in self.STRIP_TAGS:
            for tag in soup_copy.find_all(tag_name):
                tag.decompose()
        for comment in soup_copy.find_all(string=lambda t: isinstance(t, Comment)):
            comment.extract()
        text = soup_copy.get_text(separator=" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        return text