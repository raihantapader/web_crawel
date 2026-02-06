import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from crawler import WebCrawler, CrawlConfig, Page, JsonStorage


# Page Tests stores data for one crawled page)
class TestPage:
    # Test 1: When you create Page with only URL, other fields should be empty
    def test_page_defaults(self):  
        # Create page with only URL       
        page = Page(url="https://example.com")
        
        # Check all default values
        assert page.url == "https://example.com"
        assert page.title == ""
        assert page.text == ""
        assert page.links == []
        assert page.status_code == 0
        assert page.depth == 0
        assert page.error is None
    
    
    # Test 2: Create page with all data, check values are stored
    def test_page_with_data(self):
        # Create page with data
        page = Page(         
            url="https://example.com",
            title="Test",
            text="Hello world",
            links=["https://example.com/page1"],
            status_code=200,
            depth=1,
        )
        
        # Check values
        assert page.title == "Test"
        assert page.status_code == 200
        assert len(page.links) == 1

    # Test 3: converts Page to dictionary
    def test_page_to_dict(self):
        page = Page(url="https://example.com", title="Test", status_code=200)
        data = page.to_dict()   # Conv to dict
        
        # Check dictionary has correct values
        assert data["url"] == "https://example.com"
        assert data["title"] == "Test"
        assert data["status_code"] == 200
        assert "links_count" in data

    # Test 4:  Page can store error messages
    def test_page_with_error(self):
        page = Page(url="https://example.com", error="Connection failed")
        
        assert page.error == "Connection failed"  # Check


# Config Tests crawler settings
class TestCrawlConfig:
    # Test 1:  Default settings are correct
    def test_default_config(self):
        config = CrawlConfig()    # No arguments = use defaults
        
        # Check
        assert config.max_pages == 20
        assert config.max_depth == 2
        assert config.delay == 1.0
        assert config.same_domain is True
        assert config.timeout == 30

    # Test 2: Custom settings override defaults
    def test_custom_config(self):
        config = CrawlConfig(max_pages=50, max_depth=3, delay=0.5)
        
        assert config.max_pages == 50
        assert config.max_depth == 3
        assert config.delay == 0.5


# Crawler Tests main crawler
class TestWebCrawler:
    # Test 1: Crawler initializes correctly
    def test_crawler_init(self):
        crawler = WebCrawler()
        
        assert crawler.config.max_pages == 20
        assert crawler.visited == set()
        assert crawler.queue == []
        assert crawler.results == []

    # Test 2: Crawler accepts custom config
    def test_crawler_with_config(self):
        config = CrawlConfig(max_pages=10)
        crawler = WebCrawler(config)
        
        assert crawler.config.max_pages == 10

    # Test 3: Callback function is stored
    def test_crawler_with_callback(self):
        pages_received = []

        def callback(page):
            pages_received.append(page)

        crawler = WebCrawler(on_page=callback)
        assert crawler.on_page is not None  
  
    # Test 4: _parse() extracts title, text, links from HTML
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

    # Test 5: _parse() extracts meta description
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

    # Test 6: _parse() removes script and style tags from text
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


# Storage Tests class (save/load JSON)
class TestJsonStorage:
    # Test 1: Storage creates output folder
    def test_storage_init(self, tmp_path):
        storage = JsonStorage(output_dir=str(tmp_path))
        
        assert os.path.exists(tmp_path)

    # Test 2: Save pages to JSON, then load them back
    def test_save_and_load(self, tmp_path):
        storage = JsonStorage(output_dir=str(tmp_path))
        
        # Create pages
        pages = [
            Page(url="https://a.com", title="Page A", status_code=200),
            Page(url="https://b.com", title="Page B", status_code=200),
        ]
        
        # Save to file
        filepath = storage.save(pages, "test.json")
        assert os.path.exists(filepath)
        
        # Load back
        loaded = storage.load("test.json")
        assert len(loaded) == 2
        assert loaded[0]["url"] == "https://a.com"
        assert loaded[1]["title"] == "Page B"

    # Test 3: Loading missing file returns empty list
    def test_load_nonexistent(self, tmp_path):
        storage = JsonStorage(output_dir=str(tmp_path))
        result = storage.load("nonexistent.json")
        
        assert result == []

    # Test 4: Can save and load empty list
    def test_save_empty_list(self, tmp_path):
        storage = JsonStorage(output_dir=str(tmp_path))
        filepath = storage.save([], "empty.json")
        
        loaded = storage.load("empty.json")
        assert loaded == []


# Integration Test, Tests everything working together
class TestIntegration:
    # Complete workflow - config → crawler → storage
    def test_full_workflow(self, tmp_path):
        """Test complete workflow: config -> crawl setup -> storage"""
        config = CrawlConfig(max_pages=5, max_depth=1)   # 1. Create config
        crawler = WebCrawler(config)   # 2. Create crawler
        storage = JsonStorage(output_dir=str(tmp_path))    # 3. Create storage
 
        # Simulate some results
        pages = [
            Page(url="https://example.com", title="Home", status_code=200),
            Page(url="https://example.com/about", title="About", status_code=200),
        ]
        
        # Save file
        filepath = storage.save(pages)
        loaded = storage.load()

        assert len(loaded) == 2
        assert loaded[0]["title"] == "Home"
