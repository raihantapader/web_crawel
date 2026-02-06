"""Tests for data models."""
import pytest
from datetime import datetime, timezone
from crawler.models import CrawlRequest, CrawlResult, CrawlStatus, CrawlStats, PageType


class TestCrawlRequest:
    def test_defaults(self):
        req = CrawlRequest(url="https://example.com")
        assert req.depth == 0
        assert req.max_depth == 3
        assert req.priority == 0
        assert req.page_type == PageType.STATIC

    def test_url_hash_consistency(self):
        r1 = CrawlRequest(url="https://a.com")
        r2 = CrawlRequest(url="https://a.com")
        assert r1.url_hash == r2.url_hash
        assert len(r1.url_hash) == 64

    def test_equality(self):
        r1 = CrawlRequest(url="https://a.com")
        r2 = CrawlRequest(url="https://a.com", depth=5)
        r3 = CrawlRequest(url="https://b.com")
        assert r1 == r2
        assert r1 != r3
        assert len({r1, r2}) == 1


class TestCrawlResult:
    def test_to_dict(self, sample_result):
        d = sample_result.to_dict()
        assert d["url"] == "https://example.com"
        assert d["status"] == "completed"
        assert d["title"] == "Test Page"

    def test_from_dict(self, sample_result):
        d = sample_result.to_dict()
        restored = CrawlResult.from_dict(d)
        assert restored.url == sample_result.url
        assert restored.title == sample_result.title
        assert restored.status == CrawlStatus.COMPLETED


class TestCrawlStats:
    def test_duration(self):
        s = CrawlStats()
        s.start_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        s.end_time = datetime(2024, 1, 1, 0, 0, 10, tzinfo=timezone.utc)
        assert s.duration_seconds == 10.0

    def test_pages_per_second(self):
        s = CrawlStats()
        s.start_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        s.end_time = datetime(2024, 1, 1, 0, 0, 10, tzinfo=timezone.utc)
        s.total_pages_crawled = 20
        assert s.pages_per_second == 2.0

    def test_to_dict(self):
        s = CrawlStats(total_pages_crawled=10)
        s.domains_crawled.add("example.com")
        d = s.to_dict()
        assert d["total_pages_crawled"] == 10
        assert "example.com" in d["domains_crawled"]


class TestEnums:
    def test_status_values(self):
        assert CrawlStatus.COMPLETED.value == "completed"
        assert CrawlStatus.FAILED.value == "failed"
        assert CrawlStatus.SKIPPED.value == "skipped"

    def test_page_type_values(self):
        assert PageType.STATIC.value == "static"
        assert PageType.DYNAMIC.value == "dynamic"