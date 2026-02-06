"""
Rate Limiter (Requirement #4)
=============================
Per-domain rate limiting to avoid overwhelming target servers.
"""

import asyncio
import time
import logging
from collections import defaultdict
from typing import Dict

logger = logging.getLogger(__name__)


class RateLimiter:
    """Per-domain rate limiter using token bucket algorithm."""

    def __init__(
        self,
        requests_per_second: float = 2.0,
        per_domain_delay: float = 1.0,
    ):
        self.requests_per_second = requests_per_second
        self.per_domain_delay = per_domain_delay
        self._domain_last_request: Dict[str, float] = defaultdict(float)
        self._domain_locks: Dict[str, asyncio.Lock] = {}
        self._global_semaphore = asyncio.Semaphore(max(1, int(requests_per_second * 2)))
        self._domain_delays: Dict[str, float] = {}

    def _get_domain_lock(self, domain: str) -> asyncio.Lock:
        if domain not in self._domain_locks:
            self._domain_locks[domain] = asyncio.Lock()
        return self._domain_locks[domain]

    def set_domain_delay(self, domain: str, delay: float):
        """Set custom delay for a domain (e.g., from robots.txt)."""
        self._domain_delays[domain] = delay

    def get_delay_for_domain(self, domain: str) -> float:
        return self._domain_delays.get(domain, self.per_domain_delay)

    async def acquire(self, domain: str):
        """Wait until it's safe to make a request to this domain."""
        await self._global_semaphore.acquire()
        try:
            domain_lock = self._get_domain_lock(domain)
            async with domain_lock:
                now = time.monotonic()
                last = self._domain_last_request[domain]
                delay = self.get_delay_for_domain(domain)
                wait_time = delay - (now - last)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                self._domain_last_request[domain] = time.monotonic()
        finally:
            self._global_semaphore.release()

    def reset(self):
        """Clear all tracking state."""
        self._domain_last_request.clear()
        self._domain_delays.clear()
        self._domain_locks.clear()