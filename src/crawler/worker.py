"""
Crawl Worker (Requirement #5)
=============================
Async worker that processes URLs from the frontier.
"""

import asyncio
import logging
import re
from typing import Optional, Callable
from urllib.parse import urlparse

from .config import CrawlerConfig
from .fetcher import StaticFetcher, DynamicFetcher
from .frontier import BaseFrontier
from .link_extractor import LinkExtractor
from .models import CrawlRequest, CrawlResult, CrawlStatus, CrawlStats
from .parser import ContentParser
from .rate_limiter import RateLimiter
from .robots_handler import RobotsHandler
from .storage import BaseStorage

logger = logging.getLogger(__name__)


class CrawlWorker:
    """Async worker that processes URLs from the frontier."""

    def __init__(
        self,
        worker_id: int,
        config: CrawlerConfig,
        frontier: BaseFrontier,
        storage: BaseStorage,
        rate_limiter: RateLimiter,
        robots_handler: RobotsHandler,
        parser: ContentParser,
        link_extractor: LinkExtractor,
        static_fetcher: StaticFetcher,
        dynamic_fetcher: Optional[DynamicFetcher],
        stats: CrawlStats,
        on_page_crawled: Optional[Callable] = None,
    ):
        self.worker_id = worker_id
        self.config = config
        self.frontier = frontier
        self.storage = storage
        self.rate_limiter = rate_limiter
        self.robots_handler = robots_handler
        self.parser = parser
        self.link_extractor = link_extractor
        self.static_fetcher = static_fetcher
        self.dynamic_fetcher = dynamic_fetcher
        self.stats = stats
        self.on_page_crawled = on_page_crawled
        self._running = False
        self._dynamic_patterns = [
            re.compile(p, re.IGNORECASE) for p in config.dynamic_patterns
        ]

    def _should_use_dynamic(self, url: str) -> bool:
        if not self.config.enable_dynamic:
            return False
        for pattern in self._dynamic_patterns:
            if pattern.search(url):
                return True
        return False

    async def run(self, max_pages: int):
        """Main worker loop."""
        self._running = True

        while self._running:
            if self.stats.total_pages_crawled >= max_pages:
                break

            request = await self.frontier.get()
            if request is None:
                await asyncio.sleep(0.5)
                request = await self.frontier.get()
                if request is None:
                    break

            try:
                await self._process_url(request)
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                self.stats.total_pages_failed += 1

        self._running = False

    async def _process_url(self, request: CrawlRequest):
        url = request.url
        domain = urlparse(url).netloc

        # Check robots.txt
        if self.config.respect_robots:
            if not await self.robots_handler.is_allowed(url):
                self.stats.total_pages_skipped += 1
                await self.frontier.mark_visited(url)
                return

            crawl_delay = await self.robots_handler.get_crawl_delay(url)
            if crawl_delay:
                self.rate_limiter.set_domain_delay(domain, crawl_delay)

        # Rate limiting
        await self.rate_limiter.acquire(domain)
        await self.frontier.mark_visited(url)

        # Fetch
        if self._should_use_dynamic(url) and self.dynamic_fetcher:
            result = await self.dynamic_fetcher.fetch(request)
        else:
            result = await self.static_fetcher.fetch(request)

        if result.status in (CrawlStatus.FAILED, CrawlStatus.SKIPPED):
            if result.status == CrawlStatus.FAILED:
                self.stats.total_pages_failed += 1
            else:
                self.stats.total_pages_skipped += 1
            await self.storage.save(result)
            return

        # Parse
        parsed = self.parser.parse(result.html, url)
        result.title = parsed["title"]
        result.text = parsed["text"]
        result.metadata = parsed["metadata"]

        # Extract links
        links = self.link_extractor.extract_links(result.html, url)
        result.links = links

        if not self.config.store_raw_html:
            result.html = ""

        # Save
        await self.storage.save(result)

        # Update stats
        self.stats.total_pages_crawled += 1
        self.stats.total_bytes_downloaded += len(result.text.encode("utf-8"))
        self.stats.domains_crawled.add(domain)

        if self.on_page_crawled:
            try:
                self.on_page_crawled(result)
            except Exception:
                pass

        # Queue new links
        if request.depth < request.max_depth:
            for link in links:
                new_request = CrawlRequest(
                    url=link,
                    depth=request.depth + 1,
                    max_depth=request.max_depth,
                    parent_url=url,
                    priority=request.max_depth - request.depth - 1,
                )
                added = await self.frontier.add(new_request)
                if added:
                    self.stats.total_urls_found += 1

    def stop(self):
        self._running = False