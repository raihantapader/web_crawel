"""Tests for content parser."""
import pytest
from crawler.parser import ContentParser, BaseExtractor
from bs4 import BeautifulSoup


class TestContentParser:
    def test_extract_title(self, parser, sample_html):
        result = parser.parse(sample_html, "https://example.com")
        assert result["title"] == "Test Page"

    def test_extract_title_fallback_h1(self, parser):
        html = "<html><body><h1>Heading Only</h1></body></html>"
        result = parser.parse(html, "https://example.com")
        assert result["title"] == "Heading Only"

    def test_extract_text(self, parser, sample_html):
        result = parser.parse(sample_html, "https://example.com")
        assert "Test paragraph content" in result["text"]
        assert "console.log" not in result["text"]

    def test_empty_html(self, parser):
        result = parser.parse("", "https://example.com")
        assert result["title"] == ""
        assert result["text"] == ""
        assert result["metadata"] == {}

    def test_extract_description(self, parser, sample_html):
        result = parser.parse(sample_html, "https://example.com")
        assert result["metadata"]["description"] == "A test page"

    def test_extract_keywords(self, parser, sample_html):
        result = parser.parse(sample_html, "https://example.com")
        assert "test" in result["metadata"]["keywords"]
        assert "crawler" in result["metadata"]["keywords"]

    def test_extract_open_graph(self, parser, sample_html):
        result = parser.parse(sample_html, "https://example.com")
        assert result["metadata"]["open_graph"]["title"] == "OG Title"

    def test_extract_json_ld(self, parser, sample_html):
        result = parser.parse(sample_html, "https://example.com")
        assert result["metadata"]["json_ld"][0]["@type"] == "WebPage"

    def test_extract_headings(self, parser, sample_html):
        result = parser.parse(sample_html, "https://example.com")
        assert "Welcome" in result["metadata"]["headings"]["h1"]


class TestCustomExtractor:
    def test_add_custom_extractor(self, parser):
        import re

        class EmailExtractor(BaseExtractor):
            def extract(self, soup, url):
                emails = re.findall(r'[\w.-]+@[\w.-]+\.\w+', soup.get_text())
                return {"emails": emails}

        parser.add_extractor(EmailExtractor())
        html = "<html><body>Contact: info@example.com</body></html>"
        result = parser.parse(html, "https://example.com")
        assert "info@example.com" in result["metadata"]["emails"]