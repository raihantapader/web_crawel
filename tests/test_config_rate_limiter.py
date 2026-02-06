"""Tests for config and rate limiter."""
import pytest
import asyncio
import time
from crawler.config import CrawlerConfig
from crawler.rate_limiter import RateLimiter


class TestCrawlerConfig:
    def test_defaults(self):
        c = CrawlerConfig()
        assert c.max_depth == 3
        assert c.max_pages == 100
        assert c.num_workers == 4
        assert c.storage_backend == "json"

    def test_validate_success(self):
        CrawlerConfig().validate()

    def test_validate_bad_depth(self):
        with pytest.raises(ValueError, match="max_depth"):
            CrawlerConfig(max_depth=-1).validate()

    def test_validate_bad_pages(self):
        with pytest.raises(ValueError, match="max_pages"):
            CrawlerConfig(max_pages=0).validate()

    def test_validate_bad_timeout(self):
        with pytest.raises(ValueError, match="request_timeout"):
            CrawlerConfig(request_timeout=0).validate()

    def test_validate_bad_rate(self):
        with pytest.raises(ValueError, match="requests_per_second"):
            CrawlerConfig(requests_per_second=0).validate()

    def test_validate_bad_workers(self):
        with pytest.raises(ValueError, match="num_workers"):
            CrawlerConfig(num_workers=0).validate()

    def test_validate_bad_backend(self):
        with pytest.raises(ValueError, match="storage_backend"):
            CrawlerConfig(storage_backend="mysql").validate()


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_acquire(self, rate_limiter):
        await rate_limiter.acquire("example.com")

    @pytest.mark.asyncio
    async def test_per_domain_delay(self):
        limiter = RateLimiter(requests_per_second=100.0, per_domain_delay=0.2)
        t0 = time.monotonic()
        await limiter.acquire("example.com")
        await limiter.acquire("example.com")
        elapsed = time.monotonic() - t0
        assert elapsed >= 0.15

    @pytest.mark.asyncio
    async def test_different_domains_no_delay(self):
        limiter = RateLimiter(requests_per_second=100.0, per_domain_delay=1.0)
        t0 = time.monotonic()
        await limiter.acquire("a.com")
        await limiter.acquire("b.com")
        elapsed = time.monotonic() - t0
        assert elapsed < 0.5

    @pytest.mark.asyncio
    async def test_custom_delay(self):
        limiter = RateLimiter(per_domain_delay=0.05)
        limiter.set_domain_delay("slow.com", 0.3)
        assert limiter.get_delay_for_domain("slow.com") == 0.3
        assert limiter.get_delay_for_domain("fast.com") == 0.05

    @pytest.mark.asyncio
    async def test_reset(self, rate_limiter):
        await rate_limiter.acquire("example.com")
        rate_limiter.reset()
        assert len(rate_limiter._domain_last_request) == 0