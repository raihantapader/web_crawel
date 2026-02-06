"""
Web Crawler - Main Orchestrator
===============================
Entry point that initializes all components and runs the crawl.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Callable
from urllib.parse import urlparse

from .config import CrawlerConfig
from .fetcher import StaticFetcher, DynamicFetcher
from .frontier import MemoryFrontier, RedisFrontier, BaseFrontier
from .link_extractor import LinkExtractor
from .models import CrawlRequest, CrawlResult, CrawlStats
from .parser import ContentParser, BaseExtractor
from .rate_limiter import RateLimiter
from .robots_handler import RobotsHandler
from .storage import StorageFactory, BaseStorage
from .worker import CrawlWorker

logger = logging.getLogger(__name__)


class WebCrawler:
    """
    Main crawler class.
    
    Usage:
        config = CrawlerConfig(max_depth=2, max_pages=50)
        crawler = WebCrawler(config)
        stats = await crawler.crawl(["https://example.com"])
    """

    def __init__(
        self,
        config: Optional[CrawlerConfig] = None,
        custom_extractors: Optional[List[BaseExtractor]] = None,
        on_page_crawled: Optional[Callable[[CrawlResult], None]] = None,
    ):
        self.config = config or CrawlerConfig()
        self.config.validate()
        self.on_page_crawled = on_page_crawled
        self._is_running = False
        self._stats = CrawlStats()
        self._init_components(custom_extractors)

    def _init_components(self, custom_extractors=None):
        # Frontier
        if self.config.use_redis:
            self.frontier: BaseFrontier = RedisFrontier(redis_url=self.config.redis_url)
        else:
            self.frontier = MemoryFrontier()

        # Storage
        self.storage: BaseStorage = StorageFactory.create(
            self.config.storage_backend,
            storage_path=self.config.storage_path,
            mongodb_uri=self.config.mongodb_uri,
            mongodb_db=self.config.mongodb_db,
        )

        # Rate limiter
        self.rate_limiter = RateLimiter(
            requests_per_second=self.config.requests_per_second,
            per_domain_delay=self.config.per_domain_delay,
        )

        # Robots handler
        self.robots_handler = RobotsHandler(user_agent=self.config.user_agent)

        # Parser
        self.parser = ContentParser(extractors=custom_extractors)

        # Link extractor
        self.link_extractor = LinkExtractor(
            allowed_domains=self.config.allowed_domains,
            same_domain_only=self.config.same_domain_only,
            excluded_patterns=self.config.excluded_patterns,
        )

        # Fetchers
        self.static_fetcher = StaticFetcher(
            user_agent=self.config.user_agent,
            timeout=self.config.request_timeout,
            max_retries=self.config.max_retries,
            retry_delay=self.config.retry_delay,
            follow_redirects=self.config.follow_redirects,
            max_redirects=self.config.max_redirects,
        )

        self.dynamic_fetcher: Optional[DynamicFetcher] = None
        if self.config.enable_dynamic:
            self.dynamic_fetcher = DynamicFetcher(
                user_agent=self.config.user_agent,
                timeout=self.config.request_timeout,
                wait_time=self.config.dynamic_wait_time,
                max_retries=self.config.max_retries,
                retry_delay=self.config.retry_delay,
            )

    async def crawl(self, seed_urls: List[str]) -> CrawlStats:
        """Start crawling from seed URLs."""
        if not seed_urls:
            raise ValueError("At least one seed URL is required")

        self._is_running = True
        self._stats = CrawlStats()
        self._stats.start_time = datetime.now(timezone.utc)

        # Auto-populate allowed domains
        if self.config.same_domain_only and not self.config.allowed_domains:
            for url in seed_urls:
                self.config.allowed_domains.add(urlparse(url).netloc)
            self.link_extractor = LinkExtractor(
                allowed_domains=self.config.allowed_domains,
                same_domain_only=self.config.same_domain_only,
                excluded_patterns=self.config.excluded_patterns,
            )

        # Seed the frontier
        for url in seed_urls:
            request = CrawlRequest(
                url=url,
                depth=0,
                max_depth=self.config.max_depth,
                priority=100,
            )
            await self.frontier.add(request)
            self._stats.total_urls_found += 1

        # Create workers
        workers = []
        for i in range(self.config.num_workers):
            worker = CrawlWorker(
                worker_id=i,
                config=self.config,
                frontier=self.frontier,
                storage=self.storage,
                rate_limiter=self.rate_limiter,
                robots_handler=self.robots_handler,
                parser=self.parser,
                link_extractor=self.link_extractor,
                static_fetcher=self.static_fetcher,
                dynamic_fetcher=self.dynamic_fetcher,
                stats=self._stats,
                on_page_crawled=self.on_page_crawled,
            )
            workers.append(worker)

        # Run workers
        try:
            tasks = [asyncio.create_task(w.run(self.config.max_pages)) for w in workers]
            await asyncio.gather(*tasks)
        finally:
            self._is_running = False
            self._stats.end_time = datetime.now(timezone.utc)

        await self._cleanup()
        return self._stats

    async def _cleanup(self):
        try:
            await self.static_fetcher.close()
        except Exception:
            pass
        if self.dynamic_fetcher:
            try:
                await self.dynamic_fetcher.close()
            except Exception:
                pass
        try:
            await self.storage.close()
        except Exception:
            pass
        if isinstance(self.frontier, RedisFrontier):
            try:
                await self.frontier.close()
            except Exception:
                pass

    @property
    def stats(self) -> CrawlStats:
        return self._stats

    @property
    def is_running(self) -> bool:
        return self._is_running


def run_crawler(seed_urls: List[str], config: Optional[CrawlerConfig] = None) -> CrawlStats:
    """Synchronous wrapper for running the crawler."""
    config = config or CrawlerConfig()
    crawler = WebCrawler(config)
    return asyncio.run(crawler.crawl(seed_urls))