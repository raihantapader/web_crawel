import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crawler import WebCrawler, CrawlConfig, Page, JsonStorage


# Page Tests

class TestPage:
    def test_page_defaults(self):
        page = Page(url="https://example.com")
        assert page.url == "https://example.com"
        assert page.title == ""
        assert page.text == ""
        assert page.links == []
        assert page.status_code == 0
        assert page.depth == 0
        assert page.error is None

    def test_page_with_data(self):
        page = Page(
            url="https://example.com",
            title="Test",
            text="Hello world",
            links=["https://example.com/page1"],
            status_code=200,
            depth=1,
        )
        assert page.title == "Test"
        assert page.status_code == 200
        assert len(page.links) == 1

    def test_page_to_dict(self):
        page = Page(url="https://example.com", title="Test", status_code=200)
        data = page.to_dict()
        assert data["url"] == "https://example.com"
        assert data["title"] == "Test"
        assert data["status_code"] == 200
        assert "links_count" in data

    def test_page_with_error(self):
        page = Page(url="https://example.com", error="Connection failed")
        assert page.error == "Connection failed"


# Config Tests

class TestCrawlConfig:
    def test_default_config(self):
        config = CrawlConfig()
        assert config.max_pages == 20
        assert config.max_depth == 2
        assert config.delay == 1.0
        assert config.same_domain is True
        assert config.timeout == 30

    def test_custom_config(self):
        config = CrawlConfig(max_pages=50, max_depth=3, delay=0.5)
        assert config.max_pages == 50
        assert config.max_depth == 3
        assert config.delay == 0.5


# Crawler Tests

class TestWebCrawler:
    def test_crawler_init(self):
        crawler = WebCrawler()
        assert crawler.config.max_pages == 20
        assert crawler.visited == set()
        assert crawler.queue == []
        assert crawler.results == []

    def test_crawler_with_config(self):
        config = CrawlConfig(max_pages=10)
        crawler = WebCrawler(config)
        assert crawler.config.max_pages == 10

    def test_crawler_with_callback(self):
        pages_received = []

        def callback(page):
            pages_received.append(page)

        crawler = WebCrawler(on_page=callback)
        assert crawler.on_page is not None

    def test_parse_html(self):
        crawler = WebCrawler()
        crawler.domain = "example.com"
        
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Hello World</h1>
            <p>This is a test.</p>
            <a href="/page1">Link 1</a>
            <a href="https://example.com/page2">Link 2</a>
            <a href="https://other.com">External</a>
        </body>
        </html>
        """
        
        page = crawler._parse(html, "https://example.com", 200, 0)
        
        assert page.title == "Test Page"
        assert "Hello World" in page.text
        assert page.status_code == 200
        assert page.depth == 0
        assert len(page.links) >= 1  # At least internal links

    def test_parse_extracts_metadata(self):
        crawler = WebCrawler()
        crawler.domain = "example.com"
        
        html = """
        <html>
        <head>
            <title>Test</title>
            <meta name="description" content="A test page">
        </head>
        <body>Content</body>
        </html>
        """
        
        page = crawler._parse(html, "https://example.com", 200, 0)
        assert page.metadata.get("description") == "A test page"

    def test_parse_filters_scripts(self):
        crawler = WebCrawler()
        crawler.domain = "example.com"
        
        html = """
        <html>
        <body>
            <p>Real content</p>
            <script>alert('bad');</script>
            <style>.hidden{}</style>
        </body>
        </html>
        """
        
        page = crawler._parse(html, "https://example.com", 200, 0)
        assert "alert" not in page.text
        assert "hidden" not in page.text
        assert "Real content" in page.text


# Storage Tests

class TestJsonStorage:
    def test_storage_init(self, tmp_path):
        storage = JsonStorage(output_dir=str(tmp_path))
        assert os.path.exists(tmp_path)

    def test_save_and_load(self, tmp_path):
        storage = JsonStorage(output_dir=str(tmp_path))
        
        pages = [
            Page(url="https://a.com", title="Page A", status_code=200),
            Page(url="https://b.com", title="Page B", status_code=200),
        ]
        
        filepath = storage.save(pages, "test.json")
        assert os.path.exists(filepath)
        
        loaded = storage.load("test.json")
        assert len(loaded) == 2
        assert loaded[0]["url"] == "https://a.com"
        assert loaded[1]["title"] == "Page B"

    def test_load_nonexistent(self, tmp_path):
        storage = JsonStorage(output_dir=str(tmp_path))
        result = storage.load("nonexistent.json")
        assert result == []

    def test_save_empty_list(self, tmp_path):
        storage = JsonStorage(output_dir=str(tmp_path))
        filepath = storage.save([], "empty.json")
        
        loaded = storage.load("empty.json")
        assert loaded == []


# Integration Test

class TestIntegration:
    def test_full_workflow(self, tmp_path):
        """Test complete workflow: config -> crawl setup -> storage"""
        config = CrawlConfig(max_pages=5, max_depth=1)
        crawler = WebCrawler(config)
        storage = JsonStorage(output_dir=str(tmp_path))

        # Simulate some results
        pages = [
            Page(url="https://example.com", title="Home", status_code=200),
            Page(url="https://example.com/about", title="About", status_code=200),
        ]

        filepath = storage.save(pages)
        loaded = storage.load()

        assert len(loaded) == 2
        assert loaded[0]["title"] == "Home"
