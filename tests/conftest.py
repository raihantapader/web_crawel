"""Shared test fixtures."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crawler.config import CrawlerConfig
from crawler.models import CrawlRequest, CrawlResult, CrawlStatus
from crawler.frontier import MemoryFrontier
from crawler.rate_limiter import RateLimiter
from crawler.parser import ContentParser
from crawler.link_extractor import LinkExtractor
from crawler.storage import JsonStorage


@pytest.fixture
def config():
    return CrawlerConfig(
        max_depth=2, max_pages=10, same_domain_only=True,
        request_timeout=10, max_retries=1, retry_delay=0.1,
        requests_per_second=10.0, per_domain_delay=0.1,
        storage_backend="json", storage_path="/tmp/test_crawl",
        num_workers=2, respect_robots=False,
    )


@pytest.fixture
def sample_html():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Test Page</title>
        <meta name="description" content="A test page">
        <meta name="keywords" content="test, crawler">
        <meta property="og:title" content="OG Title">
        <script type="application/ld+json">{"@type":"WebPage","name":"Test"}</script>
    </head>
    <body>
        <h1>Welcome</h1>
        <p>Test paragraph content.</p>
        <a href="/page1">Page 1</a>
        <a href="/page2">Page 2</a>
        <a href="https://example.com/page3">Page 3</a>
        <a href="https://external.com/page">External</a>
        <a href="javascript:void(0)">JS</a>
        <a href="mailto:test@example.com">Email</a>
        <script>console.log("test");</script>
    </body>
    </html>
    """


@pytest.fixture
def frontier():
    return MemoryFrontier()


@pytest.fixture
def rate_limiter():
    return RateLimiter(requests_per_second=100.0, per_domain_delay=0.01)


@pytest.fixture
def parser():
    return ContentParser()


@pytest.fixture
def link_extractor():
    return LinkExtractor(
        same_domain_only=True,
        excluded_patterns=[r".*\.(jpg|png|gif)$"],
    )


@pytest.fixture
def storage(tmp_path):
    return JsonStorage(storage_path=str(tmp_path / "crawl_data"))


@pytest.fixture
def sample_result():
    return CrawlResult(
        url="https://example.com", status_code=200,
        content_type="text/html", html="<html><body>Test</body></html>",
        text="Test content", title="Test Page",
        links=["https://example.com/page1"],
        metadata={"description": "Test"},
        depth=0, elapsed_time=0.5, status=CrawlStatus.COMPLETED,
    )