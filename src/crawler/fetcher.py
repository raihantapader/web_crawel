"""
Fetcher (Requirement #1 + #4)
=============================
Static HTML fetching (aiohttp) and Dynamic JS rendering (Playwright).
Includes retry logic with exponential backoff.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict

import aiohttp

from .models import CrawlResult, CrawlStatus, CrawlRequest

logger = logging.getLogger(__name__)


class BaseFetcher(ABC):
    @abstractmethod
    async def fetch(self, request: CrawlRequest) -> CrawlResult:
        pass

    @abstractmethod
    async def close(self):
        pass


class StaticFetcher(BaseFetcher):
    """Fetches pages using plain HTTP requests (aiohttp)."""

    def __init__(
        self,
        user_agent: str = "WebCrawler/1.0",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        follow_redirects: bool = True,
        max_redirects: int = 5,
    ):
        self.user_agent = user_agent
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.follow_redirects = follow_redirects
        self.max_redirects = max_redirects
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
            }
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                headers=headers,
                timeout=timeout,
                connector=aiohttp.TCPConnector(limit=100, ssl=False),
            )
        return self._session

    async def fetch(self, request: CrawlRequest) -> CrawlResult:
        """Fetch with automatic retries and exponential backoff."""
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                return await self._do_fetch(request)
            except asyncio.TimeoutError:
                last_error = "Request timed out"
            except aiohttp.ClientError as e:
                last_error = str(e)
            except Exception as e:
                last_error = str(e)

            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** attempt)
                await asyncio.sleep(delay)

        return CrawlResult(
            url=request.url,
            depth=request.depth,
            parent_url=request.parent_url,
            status=CrawlStatus.FAILED,
            error=last_error,
        )

    async def _do_fetch(self, request: CrawlRequest) -> CrawlResult:
        session = await self._get_session()
        start_time = time.monotonic()

        async with session.get(
            request.url,
            allow_redirects=self.follow_redirects,
            max_redirects=self.max_redirects,
        ) as response:
            elapsed = time.monotonic() - start_time
            content_type = response.headers.get("Content-Type", "")

            if "text/html" not in content_type and "text/plain" not in content_type:
                return CrawlResult(
                    url=str(response.url),
                    status_code=response.status,
                    content_type=content_type,
                    depth=request.depth,
                    parent_url=request.parent_url,
                    elapsed_time=elapsed,
                    status=CrawlStatus.SKIPPED,
                    error=f"Non-HTML content: {content_type}",
                )

            html = await response.text(errors="replace")

            return CrawlResult(
                url=str(response.url),
                status_code=response.status,
                content_type=content_type,
                html=html,
                depth=request.depth,
                parent_url=request.parent_url,
                elapsed_time=elapsed,
                status=CrawlStatus.COMPLETED,
                headers=dict(response.headers),
            )

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()


class DynamicFetcher(BaseFetcher):
    """Fetches pages using headless browser (Playwright)."""

    def __init__(
        self,
        user_agent: str = "WebCrawler/1.0",
        timeout: int = 30,
        wait_time: int = 5,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self.user_agent = user_agent
        self.timeout = timeout * 1000
        self.wait_time = wait_time * 1000
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._browser = None
        self._playwright = None

    async def _ensure_browser(self):
        if self._browser is None:
            try:
                from playwright.async_api import async_playwright
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage"],
                )
            except ImportError:
                raise RuntimeError(
                    "Playwright required. Install: pip install playwright && playwright install chromium"
                )

    async def fetch(self, request: CrawlRequest) -> CrawlResult:
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                return await self._do_fetch(request)
            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))

        return CrawlResult(
            url=request.url,
            depth=request.depth,
            parent_url=request.parent_url,
            status=CrawlStatus.FAILED,
            error=last_error,
        )

    async def _do_fetch(self, request: CrawlRequest) -> CrawlResult:
        await self._ensure_browser()
        start_time = time.monotonic()

        context = await self._browser.new_context(user_agent=self.user_agent)
        page = await context.new_page()

        try:
            response = await page.goto(request.url, timeout=self.timeout, wait_until="networkidle")
            await page.wait_for_timeout(self.wait_time)
            html = await page.content()
            elapsed = time.monotonic() - start_time

            return CrawlResult(
                url=request.url,
                status_code=response.status if response else 0,
                content_type="text/html",
                html=html,
                depth=request.depth,
                parent_url=request.parent_url,
                elapsed_time=elapsed,
                status=CrawlStatus.COMPLETED,
            )
        finally:
            await page.close()
            await context.close()

    async def close(self):
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._playwright = None