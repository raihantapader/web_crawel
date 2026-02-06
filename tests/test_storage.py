"""Tests for storage backends."""
import pytest
from crawler.storage import JsonStorage, StorageFactory
from crawler.models import CrawlResult, CrawlStatus


class TestJsonStorage:
    @pytest.mark.asyncio
    async def test_save_and_get(self, storage, sample_result):
        await storage.save(sample_result)
        result = await storage.get("https://example.com")
        assert result is not None
        assert result.title == "Test Page"

    @pytest.mark.asyncio
    async def test_get_nonexistent(self, storage):
        result = await storage.get("https://nonexistent.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self, storage):
        r1 = CrawlResult(url="https://a.com", title="A", status=CrawlStatus.COMPLETED)
        r2 = CrawlResult(url="https://b.com", title="B", status=CrawlStatus.COMPLETED)
        await storage.save(r1)
        await storage.save(r2)
        all_results = await storage.get_all()
        assert len(all_results) == 2

    @pytest.mark.asyncio
    async def test_count(self, storage, sample_result):
        assert await storage.count() == 0
        await storage.save(sample_result)
        assert await storage.count() == 1

    @pytest.mark.asyncio
    async def test_clear(self, storage, sample_result):
        await storage.save(sample_result)
        await storage.clear()
        assert await storage.count() == 0

    @pytest.mark.asyncio
    async def test_overwrite(self, storage):
        r1 = CrawlResult(url="https://example.com", title="Old", status=CrawlStatus.COMPLETED)
        r2 = CrawlResult(url="https://example.com", title="New", status=CrawlStatus.COMPLETED)
        await storage.save(r1)
        await storage.save(r2)
        result = await storage.get("https://example.com")
        assert result.title == "New"
        assert await storage.count() == 1

    @pytest.mark.asyncio
    async def test_persistence(self, tmp_path):
        path = str(tmp_path / "persist_test")
        s1 = JsonStorage(storage_path=path)
        await s1.save(CrawlResult(url="https://example.com", title="Test", status=CrawlStatus.COMPLETED))
        await s1.close()

        s2 = JsonStorage(storage_path=path)
        result = await s2.get("https://example.com")
        assert result is not None
        assert result.title == "Test"


class TestStorageFactory:
    def test_create_json(self, tmp_path):
        storage = StorageFactory.create("json", storage_path=str(tmp_path))
        assert isinstance(storage, JsonStorage)

    def test_create_invalid(self):
        with pytest.raises(ValueError, match="Unknown storage backend"):
            StorageFactory.create("invalid")