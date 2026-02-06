"""Tests for URL frontier."""
import pytest
from crawler.frontier import MemoryFrontier
from crawler.models import CrawlRequest


class TestMemoryFrontier:
    @pytest.mark.asyncio
    async def test_add_and_get(self, frontier):
        req = CrawlRequest(url="https://example.com")
        assert await frontier.add(req) is True
        result = await frontier.get()
        assert result is not None
        assert result.url == "https://example.com"

    @pytest.mark.asyncio
    async def test_empty_frontier(self, frontier):
        result = await frontier.get()
        assert result is None

    @pytest.mark.asyncio
    async def test_no_duplicates(self, frontier):
        req = CrawlRequest(url="https://example.com")
        assert await frontier.add(req) is True
        assert await frontier.add(req) is False
        assert await frontier.size() == 1

    @pytest.mark.asyncio
    async def test_priority_ordering(self, frontier):
        await frontier.add(CrawlRequest(url="https://low.com", priority=1))
        await frontier.add(CrawlRequest(url="https://high.com", priority=10))
        await frontier.add(CrawlRequest(url="https://mid.com", priority=5))

        r1 = await frontier.get()
        assert r1.url == "https://high.com"
        r2 = await frontier.get()
        assert r2.url == "https://mid.com"
        r3 = await frontier.get()
        assert r3.url == "https://low.com"

    @pytest.mark.asyncio
    async def test_mark_visited(self, frontier):
        await frontier.mark_visited("https://example.com")
        assert await frontier.is_visited("https://example.com") is True
        assert await frontier.is_visited("https://other.com") is False

    @pytest.mark.asyncio
    async def test_skip_visited_on_get(self, frontier):
        await frontier.add(CrawlRequest(url="https://example.com"))
        await frontier.mark_visited("https://example.com")
        result = await frontier.get()
        assert result is None

    @pytest.mark.asyncio
    async def test_dont_add_visited(self, frontier):
        await frontier.mark_visited("https://example.com")
        result = await frontier.add(CrawlRequest(url="https://example.com"))
        assert result is False

    @pytest.mark.asyncio
    async def test_size(self, frontier):
        assert await frontier.size() == 0
        await frontier.add(CrawlRequest(url="https://a.com"))
        await frontier.add(CrawlRequest(url="https://b.com"))
        assert await frontier.size() == 2

    @pytest.mark.asyncio
    async def test_visited_count(self, frontier):
        assert await frontier.visited_count() == 0
        await frontier.mark_visited("https://a.com")
        await frontier.mark_visited("https://b.com")
        assert await frontier.visited_count() == 2

    @pytest.mark.asyncio
    async def test_clear(self, frontier):
        await frontier.add(CrawlRequest(url="https://a.com"))
        await frontier.mark_visited("https://b.com")
        await frontier.clear()
        assert await frontier.size() == 0
        assert await frontier.visited_count() == 0