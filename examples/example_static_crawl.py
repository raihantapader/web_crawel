#!/usr/bin/env python3
"""
Example 1: Crawl a Static Website
=================================
Basic example showing how to crawl a static HTML website.

Usage:
    python examples/example_static_crawl.py
    python examples/example_static_crawl.py --url https://quotes.toscrape.com --depth 2 --pages 30
"""

import asyncio
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crawler import WebCrawler, CrawlerConfig


async def main(url: str, max_depth: int, max_pages: int):
    """Run the crawler."""
    
    # Configure the crawler
    config = CrawlerConfig(
        max_depth=max_depth,
        max_pages=max_pages,
        same_domain_only=True,
        requests_per_second=2.0,
        per_domain_delay=1.0,
        storage_backend="json",
        storage_path="./output/static_crawl",
        num_workers=3,
        respect_robots=True,
    )

    # Progress callback
    def on_page_crawled(result):
        status = "✓" if result.status_code == 200 else "✗"
        print(f"  {status} [{result.status_code}] {result.url}")
        print(f"      Title: {result.title[:60]}..." if len(result.title) > 60 else f"      Title: {result.title}")
        print(f"      Links found: {len(result.links)}")

    # Create and run crawler
    crawler = WebCrawler(config, on_page_crawled=on_page_crawled)
    
    print(f"\n{'='*60}")
    print(f"🕷️  Web Crawler - Static Site Example")
    print(f"{'='*60}")
    print(f"  URL:       {url}")
    print(f"  Depth:     {max_depth}")
    print(f"  Max Pages: {max_pages}")
    print(f"{'='*60}\n")

    stats = await crawler.crawl([url])

    print(f"\n{'='*60}")
    print(f"📊 Crawl Statistics")
    print(f"{'='*60}")
    print(f"  Pages crawled:  {stats.total_pages_crawled}")
    print(f"  Pages failed:   {stats.total_pages_failed}")
    print(f"  Pages skipped:  {stats.total_pages_skipped}")
    print(f"  Duration:       {stats.duration_seconds:.2f}s")
    print(f"  Speed:          {stats.pages_per_second:.2f} pages/sec")
    print(f"  Domains:        {', '.join(stats.domains_crawled)}")
    print(f"{'='*60}")
    print(f"💾 Results saved to: ./output/static_crawl/crawl_results.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl a static website")
    parser.add_argument("--url", default="https://books.toscrape.com", help="URL to crawl")
    parser.add_argument("--depth", type=int, default=1, help="Max crawl depth")
    parser.add_argument("--pages", type=int, default=20, help="Max pages to crawl")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main(args.url, args.depth, args.pages))