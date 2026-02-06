"""
Web Crawler - Public API
========================
Production-ready, scalable web crawling system.

Quick Start:
    from crawler import WebCrawler, CrawlerConfig
    
    config = CrawlerConfig(max_depth=2, max_pages=50)
    crawler = WebCrawler(config)
    stats = await crawler.crawl(["https://example.com"])
"""

from .config import CrawlerConfig
from .crawler import WebCrawler, run_crawler
from .models import CrawlRequest, CrawlResult, CrawlStats, CrawlStatus, PageType
from .parser import ContentParser, BaseExtractor
from .fetcher import StaticFetcher, DynamicFetcher
from .frontier import MemoryFrontier, RedisFrontier
from .storage import JsonStorage, MongoStorage, StorageFactory
from .link_extractor import LinkExtractor
from .rate_limiter import RateLimiter
from .robots_handler import RobotsHandler

__version__ = "1.0.0"
__all__ = [
    "WebCrawler", "CrawlerConfig", "run_crawler",
    "CrawlRequest", "CrawlResult", "CrawlStats", "CrawlStatus", "PageType",
    "ContentParser", "BaseExtractor",
    "StaticFetcher", "DynamicFetcher",
    "MemoryFrontier", "RedisFrontier",
    "JsonStorage", "MongoStorage", "StorageFactory",
    "LinkExtractor", "RateLimiter", "RobotsHandler",
]