"""
Crawler Configuration
=====================
All crawler settings in one place with validation.
"""

from dataclasses import dataclass, field
from typing import List, Set
import os


@dataclass
class CrawlerConfig:
    """Configuration for the web crawler."""
    
    # Depth & Domain Control (Requirement #2)
    max_depth: int = 3
    max_pages: int = 100
    same_domain_only: bool = True
    allowed_domains: Set[str] = field(default_factory=set)
    excluded_patterns: List[str] = field(default_factory=lambda: [
        r".*\.(jpg|jpeg|png|gif|svg|ico|css|js|woff|woff2|ttf|eot)$",
        r".*\.(pdf|doc|docx|xls|xlsx|ppt|pptx|zip|tar|gz)$",
        r".*\.(mp3|mp4|avi|mov|wmv|flv)$",
        r".*(login|logout|signup|register|auth).*",
    ])

    # HTTP Settings (Requirement #1)
    user_agent: str = "WebCrawler/1.0 (+https://github.com/example/crawler)"
    request_timeout: int = 30
    follow_redirects: bool = True
    max_redirects: int = 5

    # Rate Limiting & Retries (Requirement #4)
    max_retries: int = 3
    retry_delay: float = 1.0
    requests_per_second: float = 2.0
    per_domain_delay: float = 1.0

    # Dynamic Rendering (Requirement #1)
    enable_dynamic: bool = False
    dynamic_wait_time: int = 5
    dynamic_patterns: List[str] = field(default_factory=list)

    # Storage (Requirement #6)
    storage_backend: str = "json"
    storage_path: str = "./crawl_output"
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    mongodb_db: str = "web_crawler"

    # Distributed Settings (Requirement #5)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    use_redis: bool = False
    num_workers: int = 4

    # Misc
    respect_robots: bool = True
    store_raw_html: bool = False

    def validate(self):
        """Validate configuration values."""
        if self.max_depth < 0:
            raise ValueError("max_depth must be >= 0")
        if self.max_pages < 1:
            raise ValueError("max_pages must be >= 1")
        if self.request_timeout < 1:
            raise ValueError("request_timeout must be >= 1")
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if self.requests_per_second <= 0:
            raise ValueError("requests_per_second must be > 0")
        if self.per_domain_delay < 0:
            raise ValueError("per_domain_delay must be >= 0")
        if self.num_workers < 1:
            raise ValueError("num_workers must be >= 1")
        if self.storage_backend not in ("json", "mongodb"):
            raise ValueError("storage_backend must be 'json' or 'mongodb'")