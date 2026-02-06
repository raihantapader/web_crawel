
"""
Example 1: Basic Web Crawl
Crawls a website and saves results to JSON.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crawler import WebCrawler, CrawlConfig, JsonStorage


async def main():
    # Settings
    url = "https://books.toscrape.com"  # Website to crawl
    
    config = CrawlConfig(
        max_pages=10,    # Stop after 10 pages
        max_depth=1,     # Only follow links 1 level
        delay=1.0,       # Wait 1 second between pages
    )

    # Progress callback
    def on_page(page):
        status = "✓" if page.status_code == 200 else "✗"
        print(f"  {status} [{page.status_code}] {page.url}")
        print(f"      Title: {page.title[:50]}")

    # Crawl
    print(f"\n🕷️  Crawling: {url}")
    print("-" * 50)

    crawler = WebCrawler(config, on_page=on_page)
    pages = await crawler.crawl(url)

    # Save
    storage = JsonStorage("output")
    filepath = storage.save(pages, "basic_crawl.json")

    print("-" * 50)
    print(f"✅ Done! Crawled {len(pages)} pages")
    print(f"💾 Saved to: {filepath}")


if __name__ == "__main__":
    asyncio.run(main())
