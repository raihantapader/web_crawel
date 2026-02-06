import asyncio
import re
from urllib.parse import urljoin, urlparse
from typing import List, Set, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

import aiohttp
from bs4 import BeautifulSoup


@dataclass
class Page:
    """One crawled page."""
    url: str
    title: str = ""
    text: str = ""
    links: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    status_code: int = 0
    depth: int = 0
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "title": self.title,
            "text": self.text[:1000],
            "links_count": len(self.links),
            "metadata": self.metadata,
            "status_code": self.status_code,
            "depth": self.depth,
            "error": self.error,
        }


@dataclass
class CrawlConfig:
    """Crawler settings."""
    max_pages: int = 20
    max_depth: int = 2
    delay: float = 1.0
    same_domain: bool = True
    timeout: int = 30


class WebCrawler:
    """Simple async web crawler."""

    def __init__(self, config: CrawlConfig = None, on_page: Callable = None):
        self.config = config or CrawlConfig()
        self.on_page = on_page
        self.visited: Set[str] = set()
        self.queue: List[tuple] = []
        self.results: List[Page] = []
        self.domain = ""

    async def crawl(self, start_url: str) -> List[Page]:
        """Crawl starting from URL."""
        self.domain = urlparse(start_url).netloc
        self.queue = [(start_url, 0)]
        self.visited = set()
        self.results = []

        async with aiohttp.ClientSession() as session:
            while self.queue and len(self.results) < self.config.max_pages:
                url, depth = self.queue.pop(0)

                if url in self.visited or depth > self.config.max_depth:
                    continue

                self.visited.add(url)
                page = await self._fetch(session, url, depth)

                if page:
                    self.results.append(page)
                    if self.on_page:
                        self.on_page(page)

                    for link in page.links:
                        if link not in self.visited:
                            self.queue.append((link, depth + 1))

                await asyncio.sleep(self.config.delay)

        return self.results

    async def _fetch(self, session, url: str, depth: int) -> Optional[Page]:
        """Fetch and parse one page."""
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            async with session.get(url, timeout=timeout) as resp:
                if "text/html" not in resp.headers.get("Content-Type", ""):
                    return None

                html = await resp.text()
                return self._parse(html, url, resp.status, depth)

        except Exception as e:
            return Page(url=url, depth=depth, error=str(e))

    def _parse(self, html: str, url: str, status: int, depth: int) -> Page:
        """Parse HTML content."""
        soup = BeautifulSoup(html, "html.parser")

        # Title
        title = soup.title.string.strip() if soup.title else ""

        # Text (remove scripts/styles)
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        text = re.sub(r"\s+", " ", soup.get_text(strip=True))

        # Metadata
        metadata = {}
        desc = soup.find("meta", {"name": "description"})
        if desc:
            metadata["description"] = desc.get("content", "")

        # Links (same domain only)
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith(("javascript:", "mailto:", "#")):
                continue
            full = urljoin(url, href)
            if self.config.same_domain and urlparse(full).netloc != self.domain:
                continue
            if not re.search(r"\.(jpg|png|gif|pdf|css|js)$", full, re.I):
                links.append(full)

        return Page(
            url=url,
            title=title,
            text=text,
            links=list(set(links)),
            metadata=metadata,
            status_code=status,
            depth=depth,
        )
