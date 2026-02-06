"""
Data Models for Web Crawler
============================
Core data structures used throughout the crawler system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, List, Any
import hashlib


class CrawlStatus(Enum):
    """Status of a crawl operation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PageType(Enum):
    """Type of page rendering required."""
    STATIC = "static"
    DYNAMIC = "dynamic"


@dataclass
class CrawlRequest:
    """Request to crawl a specific URL."""
    url: str
    depth: int = 0
    max_depth: int = 3
    parent_url: Optional[str] = None
    priority: int = 0
    page_type: PageType = PageType.STATIC

    @property
    def url_hash(self) -> str:
        return hashlib.sha256(self.url.encode()).hexdigest()

    def __hash__(self):
        return hash(self.url)

    def __eq__(self, other):
        if isinstance(other, CrawlRequest):
            return self.url == other.url
        return False


@dataclass
class CrawlResult:
    """Result from crawling a single page."""
    url: str
    status_code: int = 0
    content_type: str = ""
    html: str = ""
    text: str = ""
    title: str = ""
    links: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    crawled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    depth: int = 0
    parent_url: Optional[str] = None
    elapsed_time: float = 0.0
    status: CrawlStatus = CrawlStatus.PENDING
    error: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "text": self.text,
            "title": self.title,
            "links": self.links,
            "metadata": self.metadata,
            "crawled_at": self.crawled_at.isoformat(),
            "depth": self.depth,
            "parent_url": self.parent_url,
            "elapsed_time": self.elapsed_time,
            "status": self.status.value,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CrawlResult":
        data = data.copy()
        data["crawled_at"] = datetime.fromisoformat(data["crawled_at"])
        data["status"] = CrawlStatus(data["status"])
        data.setdefault("html", "")
        data.setdefault("headers", {})
        return cls(**data)


@dataclass
class CrawlStats:
    """Statistics for a crawl session."""
    total_urls_found: int = 0
    total_pages_crawled: int = 0
    total_pages_failed: int = 0
    total_pages_skipped: int = 0
    total_bytes_downloaded: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    domains_crawled: set = field(default_factory=set)

    @property
    def duration_seconds(self) -> float:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def pages_per_second(self) -> float:
        if self.duration_seconds > 0:
            return self.total_pages_crawled / self.duration_seconds
        return 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_urls_found": self.total_urls_found,
            "total_pages_crawled": self.total_pages_crawled,
            "total_pages_failed": self.total_pages_failed,
            "total_pages_skipped": self.total_pages_skipped,
            "total_bytes_downloaded": self.total_bytes_downloaded,
            "duration_seconds": round(self.duration_seconds, 2),
            "pages_per_second": round(self.pages_per_second, 2),
            "domains_crawled": list(self.domains_crawled),
        }