
"""
Example 3: Custom Data Extraction
Crawls and extracts specific data (prices, emails, images).
"""
import asyncio
import re
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crawler import WebCrawler, CrawlConfig


async def main():
    url = "https://books.toscrape.com"
    
    config = CrawlConfig(
        max_pages=15,
        max_depth=1,
        delay=1.0,
    )

    # Collect extracted data
    extracted = {
        "prices": [],
        "titles": [],
        "pages_with_images": 0,
    }

    def on_page(page):
        print(f"  📄 {page.url}")
        
        # Extract prices (£XX.XX format)
        prices = re.findall(r'£\d+\.\d{2}', page.text)
        if prices:
            extracted["prices"].extend(prices[:5])
            print(f"      💰 Found {len(prices)} prices")
        
        # Collect titles
        if page.title:
            extracted["titles"].append(page.title)
        
        # Count pages with images
        if "img" in page.text.lower() or "image" in page.text.lower():
            extracted["pages_with_images"] += 1

    # Crawl
    print(f"\n🕷️  Crawling with Data Extraction: {url}")
    print("-" * 50)

    crawler = WebCrawler(config, on_page=on_page)
    pages = await crawler.crawl(url)

    # Save extracted data
    os.makedirs("output", exist_ok=True)
    
    summary = {
        "url": url,
        "pages_crawled": len(pages),
        "unique_prices": list(set(extracted["prices"]))[:20],
        "price_count": len(extracted["prices"]),
        "titles": extracted["titles"][:10],
        "pages_with_images": extracted["pages_with_images"],
    }

    with open("output/extracted_data.json", "w") as f:
        json.dump(summary, f, indent=2)

    # Print summary
    print("-" * 50)
    print(f"✅ Crawled {len(pages)} pages")
    print(f"\n📊 Extraction Summary:")
    print(f"   Prices found: {len(extracted['prices'])}")
    print(f"   Unique prices: {len(set(extracted['prices']))}")
    print(f"   Sample: {list(set(extracted['prices']))[:5]}")
    print(f"\n💾 Saved to: output/extracted_data.json")


if __name__ == "__main__":
    asyncio.run(main())
