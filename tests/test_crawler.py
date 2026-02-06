"""Tests for main crawler."""
import pytest
from crawler.crawler import WebCrawler
from crawler.config import CrawlerConfig
from crawler.frontier import MemoryFrontier
from crawler.storage import JsonStorage


class TestWebCrawler:
    def test_default_config(self):
        crawler = WebCrawler()
        assert crawler.config.max_depth == 3
        assert not crawler.is_running

    def test_custom_config(self, config):
        crawler = WebCrawler(config)
        assert crawler.config.max_depth == 2

    def test_invalid_config(self):
        with pytest.raises(ValueError):
            WebCrawler(config=CrawlerConfig(max_depth=-1))

    def test_initial_stats(self):
        crawler = WebCrawler()
        assert crawler.stats.total_pages_crawled == 0

    @pytest.mark.asyncio
    async def test_empty_seeds_raises(self, config):
        crawler = WebCrawler(config)
        with pytest.raises(ValueError, match="seed URL"):
            await crawler.crawl([])

    def test_memory_frontier_default(self):
        crawler = WebCrawler()
        assert isinstance(crawler.frontier, MemoryFrontier)

    def test_json_storage_default(self):
        crawler = WebCrawler()
        assert isinstance(crawler.storage, JsonStorage)

    def test_components_initialized(self):
        crawler = WebCrawler()
        assert crawler.frontier is not None
        assert crawler.storage is not None
        assert crawler.rate_limiter is not None
        assert crawler.robots_handler is not None
        assert crawler.parser is not None
        assert crawler.link_extractor is not None
        assert crawler.static_fetcher is not None