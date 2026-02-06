
"""
Example 2: Deep Crawl
Crawls deeper into a website (more pages, more depth).
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crawler import WebCrawler, CrawlConfig, JsonStorage


async def main():
    # Settings - more pages, deeper crawl
    url = "https://quotes.toscrape.com"
    
    config = CrawlConfig(
        max_pages=30,      # More pages
        max_depth=3,       # Deeper
        delay=0.5,         # Faster
    )

    count = [0]  # Use list to modify in callback

    def on_page(page):
        count[0] += 1
        print(f"  [{count[0]:02d}] {page.title[:40]} - {page.url}")

    # Crawl
    print(f"\n🕷️  Deep Crawl: {url}")
    print(f"    Max pages: {config.max_pages}, Depth: {config.max_depth}")
    print("-" * 60)

    crawler = WebCrawler(config, on_page=on_page)
    pages = await crawler.crawl(url)

    # Save
    storage = JsonStorage("output")
    filepath = storage.save(pages, "deep_crawl.json")

    # Stats
    print("-" * 60)
    print(f"✅ Crawled {len(pages)} pages")
    
    depths = {}
    for p in pages:
        depths[p.depth] = depths.get(p.depth, 0) + 1
    
    print(f"📊 Pages by depth: {depths}")
    print(f"💾 Saved to: {filepath}")


if __name__ == "__main__":
    asyncio.run(main())
