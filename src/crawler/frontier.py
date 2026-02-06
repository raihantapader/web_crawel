"""
URL Frontier (Requirement #2 + #5)
==================================
Priority queue for URLs with deduplication.
Memory backend for single process, Redis for distributed.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional, Set
import heapq

from .models import CrawlRequest, PageType

logger = logging.getLogger(__name__)


class BaseFrontier(ABC):
    @abstractmethod
    async def add(self, request: CrawlRequest) -> bool:
        pass

    @abstractmethod
    async def get(self) -> Optional[CrawlRequest]:
        pass

    @abstractmethod
    async def mark_visited(self, url: str):
        pass

    @abstractmethod
    async def is_visited(self, url: str) -> bool:
        pass

    @abstractmethod
    async def size(self) -> int:
        pass

    @abstractmethod
    async def visited_count(self) -> int:
        pass

    @abstractmethod
    async def clear(self):
        pass


class MemoryFrontier(BaseFrontier):
    """In-memory priority queue frontier."""

    def __init__(self):
        self._queue: list = []
        self._counter: int = 0
        self._visited: Set[str] = set()
        self._in_queue: Set[str] = set()
        self._lock = asyncio.Lock()

    async def add(self, request: CrawlRequest) -> bool:
        async with self._lock:
            if request.url in self._visited or request.url in self._in_queue:
                return False
            heapq.heappush(self._queue, (-request.priority, self._counter, request))
            self._counter += 1
            self._in_queue.add(request.url)
            return True

    async def get(self) -> Optional[CrawlRequest]:
        async with self._lock:
            while self._queue:
                _, _, request = heapq.heappop(self._queue)
                self._in_queue.discard(request.url)
                if request.url not in self._visited:
                    return request
            return None

    async def mark_visited(self, url: str):
        async with self._lock:
            self._visited.add(url)

    async def is_visited(self, url: str) -> bool:
        return url in self._visited

    async def size(self) -> int:
        return len(self._queue)

    async def visited_count(self) -> int:
        return len(self._visited)

    async def clear(self):
        async with self._lock:
            self._queue.clear()
            self._visited.clear()
            self._in_queue.clear()
            self._counter = 0


class RedisFrontier(BaseFrontier):
    """Redis-backed frontier for distributed crawling."""

    QUEUE_KEY = "crawler:queue"
    VISITED_KEY = "crawler:visited"
    IN_QUEUE_KEY = "crawler:in_queue"

    def __init__(self, redis_url: str = "redis://localhost:6379", prefix: str = ""):
        self.redis_url = redis_url
        self._redis = None
        if prefix:
            self.QUEUE_KEY = f"{prefix}:{self.QUEUE_KEY}"
            self.VISITED_KEY = f"{prefix}:{self.VISITED_KEY}"
            self.IN_QUEUE_KEY = f"{prefix}:{self.IN_QUEUE_KEY}"

    async def _get_redis(self):
        if self._redis is None:
            import redis.asyncio as aioredis
            self._redis = aioredis.from_url(self.redis_url, decode_responses=True)
        return self._redis

    async def add(self, request: CrawlRequest) -> bool:
        r = await self._get_redis()
        if await r.sismember(self.VISITED_KEY, request.url):
            return False
        if await r.sismember(self.IN_QUEUE_KEY, request.url):
            return False

        data = json.dumps({
            "url": request.url,
            "depth": request.depth,
            "max_depth": request.max_depth,
            "parent_url": request.parent_url,
            "priority": request.priority,
            "page_type": request.page_type.value,
        })
        await r.zadd(self.QUEUE_KEY, {data: -request.priority})
        await r.sadd(self.IN_QUEUE_KEY, request.url)
        return True

    async def get(self) -> Optional[CrawlRequest]:
        r = await self._get_redis()
        results = await r.zpopmin(self.QUEUE_KEY, count=1)
        if not results:
            return None

        data_str, _ = results[0]
        data = json.loads(data_str)
        await r.srem(self.IN_QUEUE_KEY, data["url"])

        if await r.sismember(self.VISITED_KEY, data["url"]):
            return await self.get()

        return CrawlRequest(
            url=data["url"],
            depth=data["depth"],
            max_depth=data["max_depth"],
            parent_url=data.get("parent_url"),
            priority=data["priority"],
            page_type=PageType(data.get("page_type", "static")),
        )

    async def mark_visited(self, url: str):
        r = await self._get_redis()
        await r.sadd(self.VISITED_KEY, url)

    async def is_visited(self, url: str) -> bool:
        r = await self._get_redis()
        return await r.sismember(self.VISITED_KEY, url)

    async def size(self) -> int:
        r = await self._get_redis()
        return await r.zcard(self.QUEUE_KEY)

    async def visited_count(self) -> int:
        r = await self._get_redis()
        return await r.scard(self.VISITED_KEY)

    async def clear(self):
        r = await self._get_redis()
        await r.delete(self.QUEUE_KEY, self.VISITED_KEY, self.IN_QUEUE_KEY)

    async def close(self):
        if self._redis:
            await self._redis.close()