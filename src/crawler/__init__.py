"""
Web Crawler Package
"""
# Line 4-5: Import classes from other files
from .crawler import WebCrawler, CrawlConfig, Page
from .storage import JsonStorage

# Line 7: List of what others can use
__all__ = ["WebCrawler", "CrawlConfig", "Page", "JsonStorage"]
