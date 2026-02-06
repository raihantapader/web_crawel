"""Tests for link extractor."""
import pytest
from crawler.link_extractor import LinkExtractor


class TestLinkExtractor:
    def test_extract_absolute_urls(self):
        ext = LinkExtractor(same_domain_only=False)
        html = '<a href="https://example.com/page1">Link</a>'
        links = ext.extract_links(html, "https://example.com")
        assert "https://example.com/page1" in links

    def test_convert_relative_to_absolute(self):
        ext = LinkExtractor(same_domain_only=False)
        html = '<a href="/page1">Link</a>'
        links = ext.extract_links(html, "https://example.com")
        assert "https://example.com/page1" in links

    def test_same_domain_filter(self, link_extractor, sample_html):
        links = link_extractor.extract_links(sample_html, "https://example.com")
        for link in links:
            assert "example.com" in link
        assert "https://external.com/page" not in links

    def test_skip_javascript_links(self, link_extractor):
        html = '<a href="javascript:void(0)">JS</a>'
        links = link_extractor.extract_links(html, "https://example.com")
        assert len(links) == 0

    def test_skip_mailto_links(self, link_extractor):
        html = '<a href="mailto:test@example.com">Email</a>'
        links = link_extractor.extract_links(html, "https://example.com")
        assert len(links) == 0

    def test_skip_tel_links(self, link_extractor):
        html = '<a href="tel:1234567890">Phone</a>'
        links = link_extractor.extract_links(html, "https://example.com")
        assert len(links) == 0

    def test_skip_fragment_only_links(self, link_extractor):
        html = '<a href="#section">Anchor</a>'
        links = link_extractor.extract_links(html, "https://example.com")
        assert len(links) == 0

    def test_excluded_patterns(self):
        ext = LinkExtractor(same_domain_only=False, excluded_patterns=[r".*\.jpg$", r".*\.pdf$"])
        html = '<a href="/page">P</a><a href="/image.jpg">I</a><a href="/doc.pdf">D</a>'
        links = ext.extract_links(html, "https://example.com")
        assert "https://example.com/page" in links
        assert "https://example.com/image.jpg" not in links
        assert "https://example.com/doc.pdf" not in links

    def test_deduplication(self):
        ext = LinkExtractor(same_domain_only=False)
        html = '<a href="/page">1</a><a href="/page">2</a><a href="/page">3</a>'
        links = ext.extract_links(html, "https://example.com")
        assert links.count("https://example.com/page") == 1

    def test_normalize_trailing_slash(self):
        ext = LinkExtractor(same_domain_only=False)
        html = '<a href="/page/">Link</a>'
        links = ext.extract_links(html, "https://example.com")
        assert "https://example.com/page" in links

    def test_empty_html(self, link_extractor):
        links = link_extractor.extract_links("", "https://example.com")
        assert links == []

    def test_get_domain(self):
        assert LinkExtractor.get_domain("https://example.com/page") == "example.com"

    def test_allowed_domains(self):
        ext = LinkExtractor(allowed_domains={"a.com", "b.com"}, same_domain_only=False)
        html = '<a href="https://a.com/1">1</a><a href="https://b.com/2">2</a><a href="https://c.com/3">3</a>'
        links = ext.extract_links(html, "https://a.com")
        assert "https://a.com/1" in links
        assert "https://b.com/2" in links
        assert "https://c.com/3" not in links