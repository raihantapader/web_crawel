"""
Web Crawler Package
"""
from .crawler import WebCrawler, CrawlConfig, Page
from .storage import JsonStorage

__all__ = ["WebCrawler", "CrawlConfig", "Page", "JsonStorage"]
