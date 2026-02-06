"""
Storage (Requirement #6)
========================
Pluggable storage backends: JSON (dev) and MongoDB (production).
"""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import CrawlResult

logger = logging.getLogger(__name__)


class BaseStorage(ABC):
    @abstractmethod
    async def save(self, result: CrawlResult):
        pass

    @abstractmethod
    async def get(self, url: str) -> Optional[CrawlResult]:
        pass

    @abstractmethod
    async def get_all(self) -> List[CrawlResult]:
        pass

    @abstractmethod
    async def count(self) -> int:
        pass

    @abstractmethod
    async def clear(self):
        pass

    @abstractmethod
    async def close(self):
        pass


class JsonStorage(BaseStorage):
    """File-based JSON storage."""

    def __init__(self, storage_path: str = "./crawl_output"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._results: Dict[str, Dict[str, Any]] = {}
        self._file_path = self.storage_path / "crawl_results.json"

        if self._file_path.exists():
            try:
                with open(self._file_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            self._results[item["url"]] = item
            except (json.JSONDecodeError, KeyError):
                self._results = {}

    async def save(self, result: CrawlResult):
        self._results[result.url] = result.to_dict()
        self._write_to_file()

    async def get(self, url: str) -> Optional[CrawlResult]:
        data = self._results.get(url)
        return CrawlResult.from_dict(data) if data else None

    async def get_all(self) -> List[CrawlResult]:
        return [CrawlResult.from_dict(d) for d in self._results.values()]

    async def count(self) -> int:
        return len(self._results)

    async def clear(self):
        self._results.clear()
        if self._file_path.exists():
            self._file_path.unlink()

    async def close(self):
        self._write_to_file()

    def _write_to_file(self):
        with open(self._file_path, "w") as f:
            json.dump(list(self._results.values()), f, indent=2, default=str)


class MongoStorage(BaseStorage):
    """MongoDB storage for production."""

    def __init__(
        self,
        mongodb_uri: str = "mongodb://localhost:27017",
        database: str = "web_crawler",
        collection: str = "crawl_results",
    ):
        self.mongodb_uri = mongodb_uri
        self.database_name = database
        self.collection_name = collection
        self._client = None
        self._collection = None

    async def _ensure_connection(self):
        if self._client is None:
            from motor.motor_asyncio import AsyncIOMotorClient
            self._client = AsyncIOMotorClient(self.mongodb_uri)
            db = self._client[self.database_name]
            self._collection = db[self.collection_name]
            await self._collection.create_index("url", unique=True)
            await self._collection.create_index("crawled_at")

    async def save(self, result: CrawlResult):
        await self._ensure_connection()
        data = result.to_dict()
        data["_id"] = result.url
        await self._collection.replace_one({"_id": result.url}, data, upsert=True)

    async def get(self, url: str) -> Optional[CrawlResult]:
        await self._ensure_connection()
        data = await self._collection.find_one({"_id": url})
        if data:
            data.pop("_id", None)
            return CrawlResult.from_dict(data)
        return None

    async def get_all(self) -> List[CrawlResult]:
        await self._ensure_connection()
        results = []
        async for doc in self._collection.find():
            doc.pop("_id", None)
            results.append(CrawlResult.from_dict(doc))
        return results

    async def count(self) -> int:
        await self._ensure_connection()
        return await self._collection.count_documents({})

    async def clear(self):
        await self._ensure_connection()
        await self._collection.delete_many({})

    async def close(self):
        if self._client:
            self._client.close()


class StorageFactory:
    """Factory for creating storage backends."""

    @staticmethod
    def create(backend: str, **kwargs) -> BaseStorage:
        if backend == "json":
            return JsonStorage(storage_path=kwargs.get("storage_path", "./crawl_output"))
        elif backend == "mongodb":
            return MongoStorage(
                mongodb_uri=kwargs.get("mongodb_uri", "mongodb://localhost:27017"),
                database=kwargs.get("mongodb_db", "web_crawler"),
            )
        else:
            raise ValueError(f"Unknown storage backend: {backend}")