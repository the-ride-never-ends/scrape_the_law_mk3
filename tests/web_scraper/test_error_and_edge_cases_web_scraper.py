"""
Test Suite for Error Cases and Edge Cases in AutoScraper

Plain English Algorithms:

1. Missing Elements Tests
- Create HTML with a structure referencing non-existent elements
- Try to scrape data that should be in those elements
- Verify graceful handling with empty/null returns

2. Malformed HTML Tests
- Create HTML with unclosed tags
- Create HTML with incorrect nesting
- Create HTML with invalid attributes
- Verify parser handles these gracefully without crashing

3. Empty Response Tests
- Pass empty string as HTML
- Pass whitespace-only HTML
- Pass None as HTML
- Verify appropriate error handling

4. Giant Document Tests
- Generate very large HTML document (>1MB)
- Include target data at different depths
- Verify memory usage stays reasonable
- Verify processing time scales acceptably

5. Deep Nesting Tests
- Create HTML with >100 levels of nesting
- Put target data at various nesting levels
- Verify correct extraction without stack overflow

6. Invalid UTF-8 Tests
- Create HTML with invalid UTF-8 sequences
- Create HTML with mixed encodings
- Verify proper handling and encoding detection

7. Duplicate Content Tests
- Create HTML with identical content in different locations
- Verify proper handling of uniqueness
- Test with uniqueness enabled and disabled

8. Mixed Content Tests
- Create HTML with mixed script/style/text content
- Verify proper extraction of text without code
- Test handling of CDATA and comments

9. Special Character Tests
- Create HTML with various special characters
- Test with emoji, control characters, zero-width spaces
- Verify proper extraction and handling
"""

import pytest
from bs4 import BeautifulSoup
from typing import Optional, Any
import random
import string

from development.input_layer.autoscraper_web_scraper.auto_scraper_base_class import BaseAutoScraper
from development.input_layer.autoscraper_web_scraper.async_auto_scraper import AsyncAutoScraper
from development.input_layer.autoscraper_web_scraper.playwright_auto_scraper import PlaywrightAutoScraper


def generate_nested_html(depth: int, target_at: Optional[int] = None) -> str:
    """Generate deeply nested HTML with optional target data"""
    current = f"<div id='level-{depth}'>"
    if depth == target_at:
        current += "<span class='target'>Target Data</span>"
    if depth > 0:
        current += generate_nested_html(depth - 1, target_at)
    return current + "</div>"

def generate_large_html(size_mb: float) -> str:
    """Generate large HTML document of specified size in MB"""
    chunk = "<div>" + "".join(random.choices(string.ascii_letters, k=1000)) + "</div>\n"
    chunks_needed = int((size_mb * 1024 * 1024) / len(chunk))
    return "<html><body>" + chunk * chunks_needed + "</body></html>"

class TestErrorCases:
    """Test suite for error and edge cases"""

    @pytest.fixture
    def scraper(self):
        """Create fresh scraper instance for each test"""
        return BaseAutoScraper()

    def test_missing_elements(self, scraper):
        """Test handling of missing elements"""
        html = """
        <div class="container">
            <span class="exists">Real Data</span>
            <span class="missing"></span>
        </div>
        """
        wanted_list = ["Non-existent Data"]
        result = scraper.build(html=html, wanted_list=wanted_list)
        assert result == [], "Should return empty list for missing elements"

    def test_malformed_html(self, scraper):
        """Test handling of malformed HTML"""
        malformed_cases = [
            "<div><span>Unclosed div",
            "<div><p></div></p>",  # Incorrect nesting
            "<div invalid-attr=>Test</div>",  # Invalid attribute
        ]
        for html in malformed_cases:
            result = scraper.build(html=html, wanted_list=["Test"])
            assert isinstance(result, list), "Should handle malformed HTML without crashing"

    def test_empty_responses(self, scraper):
        """Test handling of empty responses"""
        empty_cases = ["", "   ", None]
        for html in empty_cases:
            result = scraper.build(html=html, wanted_list=["anything"])
            assert result == [], "Should handle empty input gracefully"

    @pytest.mark.slow
    def test_giant_document(self, scraper):
        """Test handling of very large documents"""
        large_html = generate_large_html(2.0)  # 2MB
        target = "SpecificTargetData"
        large_html = large_html.replace(
            "</body>", f"<div class='target'>{target}</div></body>"
        )
        
        import time
        start = time.time()
        result = scraper.build(html=large_html, wanted_list=[target])
        duration = time.time() - start
        
        assert duration < 30, "Processing should complete within reasonable time"
        assert target in result, "Should find target in large document"

    def test_deep_nesting(self, scraper):
        """Test handling of deeply nested structures"""
        depth = 100
        target = "DeepTarget"
        nested_html = generate_nested_html(depth, target_at=50)
        result = scraper.build(html=nested_html, wanted_list=[target])
        assert target in result, "Should handle deeply nested structures"

    def test_invalid_utf8(self, scraper):
        """Test handling of invalid UTF-8 sequences"""
        invalid_utf8_cases = [
            b"<div>\xFF\xFE Invalid UTF-8</div>".decode('utf-8', errors='ignore'),
            "<div>Mixed UTF-8 \u0000 Null bytes</div>",
            "<div>🌟 Unicode 🚀 Test</div>",
        ]
        for html in invalid_utf8_cases:
            result = scraper.build(html=html, wanted_list=["Test"])
            assert isinstance(result, list), "Should handle invalid UTF-8"

    def test_duplicate_content(self, scraper):
        """Test handling of duplicate content"""
        html = """
        <div class="container">
            <span class="dup">Duplicate</span>
            <div class="wrapper">
                <span class="dup">Duplicate</span>
            </div>
        </div>
        """
        # Test with uniqueness enabled
        result = scraper.build(html=html, wanted_list=["Duplicate"])
        assert len(result) == 1, "Should return unique results by default"
        
        # Test with uniqueness disabled (if supported)
        result = scraper.build(html=html, wanted_list=["Duplicate"], unique=False)
        assert len(result) == 2, "Should return all duplicates when uniqueness disabled"

    def test_mixed_content(self, scraper):
        """Test handling of mixed content types"""
        html = """
        <div>
            <script>var test = "Not This";</script>
            <style>.test { content: "Not This Either"; }</style>
            <![CDATA[Not This]]>
            <!-- Comment: Not This -->
            <span>Real Content</span>
        </div>
        """
        result = scraper.build(html=html, wanted_list=["Real Content"])
        assert "Real Content" in result, "Should extract text without code/comments"
        assert "Not This" not in result, "Should not extract script content"

    def test_special_characters(self, scraper):
        """Test handling of special characters"""
        special_cases = [
            "<div>Em🔥ji Test</div>",
            "<div>Zero-width\u200Bspace</div>",
            "<div>Control\x00Characters</div>",
            "<div>&lt;HTML&gt; Entities</div>",
            "<div>‏RTL\u202etext‎</div>",
        ]
        for html in special_cases:
            result = scraper.build(html=html, wanted_list=["Test"])
            assert isinstance(result, list), "Should handle special characters"

    def test_mutation_stability(self, scraper):
        """Test stability with DOM mutations"""
        html = """
        <div id="dynamic">
            <span class="target">Initial Content</span>
        </div>
        """
        # Simulate DOM mutation by building new soup and modifying
        soup = BeautifulSoup(html, 'lxml')
        new_element = soup.new_tag('span', attrs={'class': 'target'})
        new_element.string = 'New Content'
        soup.find(id='dynamic').append(new_element)
        
        result = scraper.build(html=str(soup), wanted_list=["Initial Content"])
        assert len(result) > 0, "Should handle DOM mutations gracefully"

    def test_base_url_handling(self, scraper):
        """Test handling of base URLs and relative paths"""
        html = """
        <base href="http://example.com/base/">
        <div>
            <a href="relative/path">Link</a>
            <img src="../image.jpg" alt="Image">
        </div>
        """
        result = scraper.build(
            html=html, 
            url="http://example.com/page", 
            wanted_list=["http://example.com/base/relative/path"]
        )
        assert len(result) > 0, "Should resolve relative URLs correctly"

    @pytest.mark.parametrize("input_size", [
        1024,      # 1KB
        1024*1024, # 1MB
        5*1024*1024, # 5MB
    ])
    def test_memory_scaling(self, scraper, input_size):
        """Test memory usage with different input sizes"""
        import resource
        import os
        
        # Generate HTML of specified size
        html = generate_large_html(input_size / (1024*1024))  # Convert to MB
        
        # Measure memory before
        before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        # Run scraper
        result = scraper.build(html=html, wanted_list=["Test"])
        
        # Measure memory after
        after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        
        # Check memory usage didn't grow more than 10x input size
        memory_growth = after - before
        assert memory_growth < input_size * 10, "Memory usage grew too much"

if __name__ == "__main__":
    pytest.main([__file__])