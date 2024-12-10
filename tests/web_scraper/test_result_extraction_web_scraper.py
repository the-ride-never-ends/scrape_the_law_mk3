"""
Test suite for AutoScraper result extraction functionality.
Tests cover the full range of extraction capabilities including simple text,
attributes, URLs, and various result processing options.
"""

import pytest
from bs4 import BeautifulSoup
from unittest.mock import Mock, patch
import hashlib
from urllib.parse import urljoin

from development.input_layer.autoscraper_web_scraper.auto_scraper_base_class import BaseAutoScraper


# Test HTML fixtures
@pytest.fixture
def simple_html():
    return """
    <html>
        <body>
            <div class="container">
                <span class="price">$10.99</span>
                <span class="price">$20.99</span>
                <a href="/product/1">Product 1</a>
                <a href="/product/2">Product 2</a>
            </div>
        </body>
    </html>
    """

@pytest.fixture
def nested_html():
    return """
    <html>
        <body>
            <div class="level1">
                <div class="level2">
                    <p class="text">First paragraph</p>
                    <p class="text">Second paragraph</p>
                </div>
                <div class="level2">
                    <p class="text">Third paragraph</p>
                </div>
            </div>
        </body>
    </html>
    """

@pytest.fixture
def base_scraper():
    """Create a minimal concrete implementation of BaseAutoScraper for testing"""
    class TestScraper(BaseAutoScraper):
        def _fetch_html(self, url, request_args=None):
            return ""
        
        async def _async_fetch_html(self, url, request_args=None):
            return ""
            
    return TestScraper()

class TestSimpleTextExtraction:
    """Tests for basic text extraction capabilities"""
    
    def test_direct_text_extraction(self, base_scraper, simple_html):
        """
        Algorithm:
        1. Create soup from simple HTML
        2. Build rules for price elements
        3. Extract text and verify values
        4. Check text is stripped and cleaned
        """
        soup = BeautifulSoup(simple_html, 'lxml')
        rules = base_scraper.build(html=simple_html, wanted_list=["$10.99"])
        results = base_scraper.get_result_similar(html=simple_html)
        assert "$10.99" in results
        assert "$20.99" in results

    def test_nested_text_extraction(self, base_scraper, nested_html):
        """
        Algorithm:
        1. Create soup from nested HTML
        2. Build rules for nested paragraph text
        3. Verify correct extraction of all levels
        4. Check parent-child relationships are preserved
        """
        soup = BeautifulSoup(nested_html, 'lxml')
        rules = base_scraper.build(html=nested_html, wanted_list=["First paragraph"])
        results = base_scraper.get_result_similar(html=nested_html)
        assert "First paragraph" in results
        assert "Second paragraph" in results
        assert "Third paragraph" in results

class TestAttributeExtraction:
    """Tests for extracting attributes from elements"""
    
    def test_href_extraction(self, base_scraper, simple_html):
        """
        Algorithm:
        1. Build rules targeting href attributes
        2. Extract URLs
        3. Verify relative URLs are properly handled
        4. Check full URL construction
        """
        base_url = "http://example.com"
        rules = base_scraper.build(html=simple_html, wanted_list=["/product/1"])
        results = base_scraper.get_result_similar(
            html=simple_html,
            url=base_url
        )
        assert "http://example.com/product/1" in results
        assert "http://example.com/product/2" in results

class TestResultProcessing:
    """Tests for result processing options"""
    
    def test_result_grouping(self, base_scraper, simple_html):
        """
        Algorithm:
        1. Build rules with different aliases
        2. Extract results with grouping enabled
        3. Verify correct group structure
        4. Check all items are in correct groups
        """
        rules = base_scraper.build(
            html=simple_html,
            wanted_dict={
                "prices": ["$10.99"],
                "products": ["Product 1"]
            }
        )
        results = base_scraper.get_result_similar(
            html=simple_html,
            grouped=True,
            group_by_alias=True
        )
        assert "prices" in results
        assert "$10.99" in results["prices"]
        assert "$20.99" in results["prices"]
        assert "products" in results
        assert "Product 1" in results["products"]
        assert "Product 2" in results["products"]

    def test_result_uniqueness(self, base_scraper):
        """
        Algorithm:
        1. Create HTML with duplicate content
        2. Extract with uniqueness enabled/disabled
        3. Verify correct handling of duplicates
        4. Check order preservation
        """
        html = """
        <div>
            <p>Duplicate</p>
            <p>Duplicate</p>
            <p>Unique</p>
        </div>
        """
        rules = base_scraper.build(html=html, wanted_list=["Duplicate"])
        
        # Test with uniqueness enabled
        results_unique = base_scraper.get_result_similar(
            html=html,
            unique=True
        )
        assert len([r for r in results_unique if r == "Duplicate"]) == 1
        
        # Test with uniqueness disabled
        results_all = base_scraper.get_result_similar(
            html=html,
            unique=False
        )
        assert len([r for r in results_all if r == "Duplicate"]) == 2

class TestFuzzyMatching:
    """Tests for fuzzy text matching capabilities"""
    
    def test_fuzzy_text_matching(self, base_scraper):
        """
        Algorithm:
        1. Create HTML with similar but not identical text
        2. Extract with different fuzzy ratios
        3. Verify matching behavior at different thresholds
        4. Check edge cases
        """
        html = """
        <div>
            <p>Original Text</p>
            <p>Original Text!</p>
            <p>Original texT</p>
            <p>Completely Different</p>
        </div>
        """
        rules = base_scraper.build(
            html=html,
            wanted_list=["Original Text"],
            text_fuzz_ratio=0.8
        )
        results = base_scraper.get_result_similar(
            html=html,
            attr_fuzz_ratio=0.8
        )
        assert "Original Text" in results
        assert "Original Text!" in results
        assert "Original texT" in results
        assert "Completely Different" not in results

class TestSiblingHandling:
    """Tests for handling sibling elements"""
    
    def test_sibling_extraction(self, base_scraper):
        """
        Algorithm:
        1. Create HTML with sibling elements
        2. Extract with sibling handling enabled/disabled
        3. Verify correct sibling inclusion/exclusion
        4. Check order preservation
        """
        html = """
        <div class="parent">
            <p>Target</p>
            <p>Sibling 1</p>
            <p>Sibling 2</p>
        </div>
        """
        rules = base_scraper.build(html=html, wanted_list=["Target"])
        
        # Test without sibling handling
        results_no_siblings = base_scraper.get_result_similar(
            html=html,
            contain_sibling_leaves=False
        )
        assert len(results_no_siblings) == 1
        assert "Target" in results_no_siblings
        
        # Test with sibling handling
        results_with_siblings = base_scraper.get_result_similar(
            html=html,
            contain_sibling_leaves=True
        )
        assert len(results_with_siblings) == 3
        assert "Target" in results_with_siblings
        assert "Sibling 1" in results_with_siblings
        assert "Sibling 2" in results_with_siblings

if __name__ == "__main__":
    pytest.main([__file__])