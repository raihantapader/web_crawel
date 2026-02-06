#!/usr/bin/env python3
"""
Example 2: Crawl a Dynamic (JavaScript) Website
===============================================
Example showing how to crawl JavaScript-rendered pages using Playwright.

Requires: pip install playwright && playwright install chromium

Usage:
    python examples/example_dynamic_crawl.py
"""

import asyncio
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crawler import WebCrawler, CrawlerConfig


async def main(url: str, max_depth: int, max_pages: int):
    """Run the dynamic crawler."""
    
    # Configure for dynamic content
    config = CrawlerConfig(
        max_depth=max_depth,
        max_pages=max_pages,
        same_domain_only=True,
        
        # Enable dynamic rendering
        enable_dynamic=True,
        dynamic_wait_time=3,  # Wait 3 seconds for JS to load
        dynamic_patterns=[r".*"],  # Use browser for all URLs
        
        requests_per_second=1.0,  # Slower for browser
        per_domain_delay=2.0,
        storage_backend="json",
        storage_path="./output/dynamic_crawl",
        num_workers=2,  # Fewer workers (browser is heavy)
        request_timeout=30,
    )

    def on_page_crawled(result):
        status = "✓" if result.status_code == 200 else "✗"
        title = result.title[:50] + "..." if len(result.title) > 50 else result.title
        print(f"  {status} {result.url}")
        print(f"      Title: {title}")

    crawler = WebCrawler(config, on_page_crawled=on_page_crawled)
    
    print(f"\n{'='*60}")
    print(f"🕷️  Web Crawler - Dynamic Site Example (Playwright)")
    print(f"{'='*60}")
    print(f"  URL:       {url}")
    print(f"  Depth:     {max_depth}")
    print(f"  Max Pages: {max_pages}")
    print(f"  Browser:   Chromium (headless)")
    print(f"{'='*60}\n")

    try:
        stats = await crawler.crawl([url])

        print(f"\n{'='*60}")
        print(f"📊 Crawl Statistics")
        print(f"{'='*60}")
        print(f"  Pages crawled:  {stats.total_pages_crawled}")
        print(f"  Pages failed:   {stats.total_pages_failed}")
        print(f"  Duration:       {stats.duration_seconds:.2f}s")
        print(f"{'='*60}")
        print(f"💾 Results saved to: ./output/dynamic_crawl/crawl_results.json")
        
    except RuntimeError as e:
        if "Playwright" in str(e):
            print("\n❌ Playwright not installed!")
            print("   Run: pip install playwright && playwright install chromium")
        else:
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl a dynamic website")
    parser.add_argument("--url", default="https://quotes.toscrape.com/js/", help="URL to crawl")
    parser.add_argument("--depth", type=int, default=1, help="Max crawl depth")
    parser.add_argument("--pages", type=int, default=10, help="Max pages to crawl")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main(args.url, args.depth, args.pages))