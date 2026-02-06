"""
Robots.txt Handler
==================
Fetches and caches robots.txt for each domain.
"""

import asyncio
import logging
from typing import Dict, Optional
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import aiohttp

logger = logging.getLogger(__name__)


class RobotsHandler:
    """Handles robots.txt compliance."""

    def __init__(self, user_agent: str = "WebCrawler/1.0", timeout: int = 10):
        self.user_agent = user_agent
        self.timeout = timeout
        self._cache: Dict[str, Optional[RobotFileParser]] = {}
        self._lock = asyncio.Lock()

    async def _fetch_robots(self, domain: str, scheme: str = "https") -> Optional[RobotFileParser]:
        robots_url = f"{scheme}://{domain}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(robots_url) as response:
                    if response.status == 200:
                        text = await response.text()
                        rp.parse(text.splitlines())
                        return rp
                    rp.parse([])
                    return rp
        except Exception as e:
            logger.debug(f"Error fetching robots.txt for {domain}: {e}")
            rp.parse([])
            return rp

    async def get_parser(self, url: str) -> Optional[RobotFileParser]:
        parsed = urlparse(url)
        domain = parsed.netloc
        scheme = parsed.scheme or "https"

        async with self._lock:
            if domain not in self._cache:
                self._cache[domain] = await self._fetch_robots(domain, scheme)
        return self._cache.get(domain)

    async def is_allowed(self, url: str) -> bool:
        parser = await self.get_parser(url)
        if parser is None:
            return True
        try:
            return parser.can_fetch(self.user_agent, url)
        except Exception:
            return True

    async def get_crawl_delay(self, url: str) -> Optional[float]:
        parser = await self.get_parser(url)
        if parser is None:
            return None
        try:
            delay = parser.crawl_delay(self.user_agent)
            return float(delay) if delay is not None else None
        except Exception:
            return None

    def clear_cache(self):
        self._cache.clear()