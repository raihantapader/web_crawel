#!/usr/bin/env python3
"""
Example 3: Crawl with Custom Data Extractors
============================================
Example showing how to create custom extractors for specific data.

Usage:
    python examples/example_custom_extractors.py
"""

import asyncio
import json
import re
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bs4 import BeautifulSoup
from crawler import WebCrawler, CrawlerConfig, BaseExtractor


# ─────────────────────────────────────────────────────────────
# Custom Extractors
# ─────────────────────────────────────────────────────────────

class PriceExtractor(BaseExtractor):
    """Extract prices from pages (e.g., $19.99, £24.50)."""
    
    def extract(self, soup: BeautifulSoup, url: str):
        # Find price patterns
        text = soup.get_text()
        prices = re.findall(r'[$£€]\s*\d+[.,]?\d*', text)
        
        # Also check common price classes
        price_elements = soup.find_all(class_=re.compile(r'price', re.I))
        for elem in price_elements:
            price_text = elem.get_text(strip=True)
            if price_text and price_text not in prices:
                prices.append(price_text)
        
        return {"prices": list(set(prices))[:10]} if prices else {}


class EmailExtractor(BaseExtractor):
    """Extract email addresses from pages."""
    
    def extract(self, soup: BeautifulSoup, url: str):
        emails = set()
        
        # Regex pattern for emails
        text = soup.get_text()
        found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        emails.update(found)
        
        # Check mailto: links
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("mailto:"):
                email = href.replace("mailto:", "").split("?")[0]
                if email:
                    emails.add(email)
        
        return {"emails": list(emails)} if emails else {}


class ImageStatsExtractor(BaseExtractor):
    """Extract image statistics from pages."""
    
    def extract(self, soup: BeautifulSoup, url: str):
        images = soup.find_all("img")
        
        if not images:
            return {}
        
        stats = {
            "total_images": len(images),
            "images_with_alt": sum(1 for img in images if img.get("alt")),
            "images_without_alt": sum(1 for img in images if not img.get("alt")),
        }
        
        # Get image sources
        sources = []
        for img in images[:5]:  # First 5 images
            src = img.get("src", "")
            alt = img.get("alt", "")
            if src:
                sources.append({"src": src, "alt": alt})
        
        stats["sample_images"] = sources
        return {"image_stats": stats}


class ProductExtractor(BaseExtractor):
    """Extract product information (for e-commerce sites)."""
    
    def extract(self, soup: BeautifulSoup, url: str):
        products = []
        
        # Common product container patterns
        product_containers = soup.find_all(class_=re.compile(r'product|item|card', re.I))
        
        for container in product_containers[:5]:
            product = {}
            
            # Title
            title = container.find(['h2', 'h3', 'h4'])
            if not title:
                title = container.find(class_=re.compile(r'title|name', re.I))
            if title:
                product["name"] = title.get_text(strip=True)
            
            # Price
            price = container.find(class_=re.compile(r'price', re.I))
            if price:
                product["price"] = price.get_text(strip=True)
            
            # Rating
            rating = container.find(class_=re.compile(r'rating|star', re.I))
            if rating:
                product["rating"] = rating.get_text(strip=True)
            
            if product:
                products.append(product)
        
        return {"products": products} if products else {}


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

async def main():
    url = "https://books.toscrape.com"
    
    config = CrawlerConfig(
        max_depth=1,
        max_pages=15,
        same_domain_only=True,
        requests_per_second=2.0,
        per_domain_delay=1.0,
        storage_backend="json",
        storage_path="./output/custom_extraction",
        num_workers=3,
    )

    # Create custom extractors
    custom_extractors = [
        PriceExtractor(),
        EmailExtractor(),
        ImageStatsExtractor(),
        ProductExtractor(),
    ]

    # Collect extracted data
    extracted_data = []

    def on_page_crawled(result):
        status = "✓" if result.status_code == 200 else "✗"
        print(f"\n  {status} {result.url}")
        
        metadata = result.metadata or {}
        
        # Show extracted data
        if metadata.get("prices"):
            print(f"      💰 Prices: {', '.join(metadata['prices'][:5])}")
        
        if metadata.get("emails"):
            print(f"      📧 Emails: {', '.join(metadata['emails'][:3])}")
        
        if metadata.get("image_stats"):
            stats = metadata["image_stats"]
            print(f"      🖼️  Images: {stats['total_images']} total, {stats['images_with_alt']} with alt")
        
        if metadata.get("products"):
            print(f"      📦 Products: {len(metadata['products'])} found")
        
        # Collect for summary
        extracted_data.append({
            "url": result.url,
            "title": result.title,
            "prices": metadata.get("prices", []),
            "emails": metadata.get("emails", []),
            "image_stats": metadata.get("image_stats"),
            "products": metadata.get("products", []),
        })

    crawler = WebCrawler(
        config, 
        custom_extractors=custom_extractors,
        on_page_crawled=on_page_crawled
    )

    print(f"\n{'='*60}")
    print(f"🕷️  Web Crawler - Custom Extractors Example")
    print(f"{'='*60}")
    print(f"  URL:        {url}")
    print(f"  Extractors: PriceExtractor, EmailExtractor,")
    print(f"              ImageStatsExtractor, ProductExtractor")
    print(f"{'='*60}")

    stats = await crawler.crawl([url])

    print(f"\n{'='*60}")
    print(f"📊 Crawl Statistics")
    print(f"{'='*60}")
    print(f"  Pages crawled:  {stats.total_pages_crawled}")
    print(f"  Duration:       {stats.duration_seconds:.2f}s")
    
    # Summary of extracted data
    all_prices = set()
    all_emails = set()
    total_images = 0
    total_products = 0
    
    for data in extracted_data:
        all_prices.update(data.get("prices", []))
        all_emails.update(data.get("emails", []))
        if data.get("image_stats"):
            total_images += data["image_stats"]["total_images"]
        total_products += len(data.get("products", []))
    
    print(f"\n📋 Extraction Summary:")
    print(f"  Unique prices found:  {len(all_prices)}")
    print(f"  Unique emails found:  {len(all_emails)}")
    print(f"  Total images found:   {total_images}")
    print(f"  Products extracted:   {total_products}")
    print(f"{'='*60}")
    
    # Save extracted data to separate file
    os.makedirs("./output/custom_extraction", exist_ok=True)
    with open("./output/custom_extraction/extracted_data.json", "w") as f:
        json.dump(extracted_data, f, indent=2)
    
    print(f"💾 Results saved to: ./output/custom_extraction/")
    print(f"   - crawl_results.json (full crawl data)")
    print(f"   - extracted_data.json (custom extraction summary)")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())