# 🕷️ Generic Web Crawling System

A production-ready, scalable web crawling system that can crawl both static and dynamic websites, extract structured data, and handle various edge cases at scale.

## 📋 Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Docker Setup](#docker-setup)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Project Structure](#project-structure)
- [Testing](#testing)
- [Design Decisions](#design-decisions)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WEB CRAWLER ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   SEED URLs                                                                 │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ REQUIREMENT #1: Static & Dynamic Fetching                            │   │
│  │ ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐  │   │
│  │ │  StaticFetcher  │    │  DynamicFetcher  │    │  RobotsHandler  │  │   │
│  │ │    (aiohttp)    │    │   (Playwright)   │    │  (robots.txt)   │  │   │
│  │ └────────┬────────┘    └────────┬─────────┘    └────────┬────────┘  │   │
│  └──────────┼──────────────────────┼───────────────────────┼───────────┘   │
│             │                      │                       │               │
│             ▼                      ▼                       ▼               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ REQUIREMENT #2: Link Discovery & Control                             │   │
│  │ ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐  │   │
│  │ │  LinkExtractor  │    │   URL Frontier   │    │  CrawlerConfig  │  │   │
│  │ │  (normalize,    │    │  (priority queue │    │  (depth, domain │  │   │
│  │ │   filter URLs)  │    │   + dedup)       │    │   control)      │  │   │
│  │ └────────┬────────┘    └────────┬─────────┘    └────────┬────────┘  │   │
│  └──────────┼──────────────────────┼───────────────────────┼───────────┘   │
│             │                      │                       │               │
│             ▼                      ▼                       ▼               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ REQUIREMENT #3: Content Extraction                                   │   │
│  │ ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐  │   │
│  │ │  ContentParser  │    │ MetadataExtractor│    │ Custom Extractors│  │   │
│  │ │  (title, text)  │    │ (OG, JSON-LD)    │    │  (pluggable)    │  │   │
│  │ └────────┬────────┘    └────────┬─────────┘    └────────┬────────┘  │   │
│  └──────────┼──────────────────────┼───────────────────────┼───────────┘   │
│             │                      │                       │               │
│             ▼                      ▼                       ▼               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ REQUIREMENT #4: Rate Limiting & Error Handling                       │   │
│  │ ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐  │   │
│  │ │   RateLimiter   │    │   Retry Logic    │    │  Error Tracking │  │   │
│  │ │  (per-domain)   │    │ (exp. backoff)   │    │  (CrawlStatus)  │  │   │
│  │ └────────┬────────┘    └────────┬─────────┘    └────────┬────────┘  │   │
│  └──────────┼──────────────────────┼───────────────────────┼───────────┘   │
│             │                      │                       │               │
│             ▼                      ▼                       ▼               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ REQUIREMENT #5: Distributed Workers                                  │   │
│  │ ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐  │   │
│  │ │   CrawlWorker   │    │   WebCrawler     │    │  RedisFrontier  │  │   │
│  │ │  (async tasks)  │    │  (orchestrator)  │    │  (distributed)  │  │   │
│  │ └────────┬────────┘    └────────┬─────────┘    └────────┬────────┘  │   │
│  └──────────┼──────────────────────┼───────────────────────┼───────────┘   │
│             │                      │                       │               │
│             ▼                      ▼                       ▼               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │ REQUIREMENT #6: Storage                                              │   │
│  │ ┌─────────────────┐    ┌──────────────────┐                         │   │
│  │ │   JsonStorage   │    │   MongoStorage   │                         │   │
│  │ │  (development)  │    │   (production)   │                         │   │
│  │ └─────────────────┘    └──────────────────┘                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input**: Seed URLs + Configuration
2. **Fetch**: StaticFetcher (aiohttp) or DynamicFetcher (Playwright)
3. **Parse**: Extract title, text, metadata, links
4. **Queue**: Add discovered links to priority frontier
5. **Rate Limit**: Per-domain delays with exponential backoff
6. **Store**: Save results to JSON or MongoDB

---

## 🚀 Quick Start

### Local Installation

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/web-crawler.git
cd web-crawler

# Install dependencies
pip install -r requirements.txt

# Run example
python examples/example_static_crawl.py
```

### Docker (Recommended)

```bash
# Build and run
docker compose build
docker compose up

# Run tests
docker compose --profile test run tests
```

---

## 🐳 Docker Setup

### Prerequisites

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Start Docker Desktop and wait for "Engine running"

### Commands

| Action | Command |
|--------|---------|
| Build images | `docker compose build` |
| Run crawler | `docker compose up` |
| Run tests | `docker compose --profile test run tests` |
| Stop all | `docker compose down` |
| Full cleanup | `docker compose down --rmi all --volumes` |

### Custom Crawl

```bash
# Crawl any website
docker compose run --rm crawler python examples/example_static_crawl.py \
    --url https://quotes.toscrape.com \
    --depth 2 \
    --pages 50
```

---

## 📖 Usage Examples

### Example 1: Basic Static Crawl

```python
import asyncio
from crawler import WebCrawler, CrawlerConfig

async def main():
    config = CrawlerConfig(
        max_depth=2,
        max_pages=50,
        same_domain_only=True,
    )
    
    crawler = WebCrawler(config)
    stats = await crawler.crawl(["https://example.com"])
    
    print(f"Crawled {stats.total_pages_crawled} pages")

asyncio.run(main())
```

### Example 2: Dynamic (JavaScript) Sites

```python
config = CrawlerConfig(
    enable_dynamic=True,
    dynamic_wait_time=5,
    dynamic_patterns=[r".*"],  # Use browser for all URLs
)

crawler = WebCrawler(config)
await crawler.crawl(["https://spa-site.com"])
```

### Example 3: Custom Extractors

```python
from crawler import BaseExtractor
import re

class PriceExtractor(BaseExtractor):
    def extract(self, soup, url):
        prices = re.findall(r'\$\d+\.\d{2}', soup.get_text())
        return {"prices": prices}

crawler = WebCrawler(config, custom_extractors=[PriceExtractor()])
```

### Example 4: Distributed Mode (Redis)

```python
config = CrawlerConfig(
    use_redis=True,
    redis_url="redis://localhost:6379",
    num_workers=8,
)
```

---

## ⚙️ Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_depth` | 3 | Maximum link depth from seed URLs |
| `max_pages` | 100 | Maximum pages to crawl |
| `same_domain_only` | True | Stay on seed domain |
| `max_retries` | 3 | Retry attempts on failure |
| `requests_per_second` | 2.0 | Global rate limit |
| `per_domain_delay` | 1.0 | Delay between requests to same domain |
| `enable_dynamic` | False | Use Playwright for JS rendering |
| `dynamic_wait_time` | 5 | Seconds to wait for JS to load |
| `storage_backend` | "json" | "json" or "mongodb" |
| `use_redis` | False | Use Redis for distributed queue |
| `num_workers` | 4 | Number of concurrent workers |
| `respect_robots` | True | Obey robots.txt rules |

---

## 📁 Project Structure

```
web-crawler/
├── src/
│   └── crawler/
│       ├── __init__.py      # Public API exports
│       ├── models.py        # Data classes (CrawlRequest, CrawlResult)
│       ├── config.py        # CrawlerConfig with validation
│       ├── crawler.py       # Main WebCrawler orchestrator
│       ├── worker.py        # Async CrawlWorker
│       ├── fetcher.py       # StaticFetcher + DynamicFetcher
│       ├── parser.py        # ContentParser + extractors
│       ├── link_extractor.py# URL discovery and filtering
│       ├── frontier.py      # MemoryFrontier + RedisFrontier
│       ├── storage.py       # JsonStorage + MongoStorage
│       ├── rate_limiter.py  # Per-domain rate limiting
│       └── robots_handler.py# robots.txt compliance
├── tests/
│   ├── conftest.py          # Shared fixtures
│   ├── test_models.py
│   ├── test_config_rate_limiter.py
│   ├── test_parser.py
│   ├── test_link_extractor.py
│   ├── test_frontier.py
│   ├── test_storage.py
│   └── test_crawler.py
├── examples/
│   ├── example_static_crawl.py
│   ├── example_dynamic_crawl.py
│   └── example_custom_extractors.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=src/crawler --cov-report=term-missing

# Docker
docker compose --profile test run tests
```

**Coverage Target: >70%**

---

## 🎯 Design Decisions

### 1. Async-First Architecture
- Uses `asyncio` for high concurrency without threads
- `aiohttp` for non-blocking HTTP requests
- Supports hundreds of concurrent requests efficiently

### 2. Pluggable Components
- **Fetchers**: StaticFetcher (fast) or DynamicFetcher (JS support)
- **Storage**: JsonStorage (dev) or MongoStorage (production)
- **Frontier**: MemoryFrontier (single process) or RedisFrontier (distributed)
- **Extractors**: Add custom extractors without modifying core code

### 3. Per-Domain Rate Limiting
- Each domain has its own rate bucket
- Respects `robots.txt` crawl-delay
- Global semaphore caps total concurrent requests

### 4. Robust Error Handling
- Exponential backoff retry logic (1s, 2s, 4s delays)
- Graceful handling of timeouts, network errors
- Status tracking (COMPLETED, FAILED, SKIPPED)

### 5. Distributed Support
- Redis-backed frontier for multi-instance crawling
- Multiple crawler processes share the same URL queue
- Horizontal scaling via Docker Compose

---

## 📄 License

MIT License
#   w e b _ c r a w l e r  
 