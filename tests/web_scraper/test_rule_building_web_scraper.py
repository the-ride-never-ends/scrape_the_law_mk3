"""
Test Suite for BaseAutoScraper Rule Building

Plain English Algorithms:

1. Basic Rule Building
   - Given: Simple HTML with a target text in a paragraph
   - When: Building rules with the target text
   - Then: Should create a rule matching the paragraph structure
   
2. Nested Element Rules
   - Given: HTML with target text nested in multiple divs
   - When: Building rules for the target text
   - Then: Should create a rule capturing the complete element hierarchy

3. Multiple Rules from Same Structure
   - Given: HTML with multiple similar elements (like a list)
   - When: Building rules for multiple target texts
   - Then: Should create unique rules for each target

4. Regular Expression Rules
   - Given: HTML with text matching a pattern
   - When: Building rules using regex patterns
   - Then: Should create rules matching the pattern

5. Rule Updating
   - Given: Existing rules and new target text
   - When: Building rules with update=True
   - Then: Should append new rules while keeping existing ones

Python Implementation:
"""

import pytest
from bs4 import BeautifulSoup
import re
from unittest.mock import Mock, patch


from development.input_layer.autoscraper_web_scraper.auto_scraper_base_class import BaseAutoScraper


# Test Fixtures
@pytest.fixture
def simple_html():
    return """
    <html>
        <body>
            <div class="content">
                <p class="target">Target Text</p>
                <p class="other">Other Text</p>
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
                    <div class="level3">
                        <span class="target">Nested Target</span>
                    </div>
                </div>
            </div>
        </body>
    </html>
    """

@pytest.fixture
def list_html():
    return """
    <html>
        <body>
            <ul>
                <li class="item">First Item</li>
                <li class="item">Second Item</li>
                <li class="item">Third Item</li>
            </ul>
        </body>
    </html>
    """

# Basic Rule Building Tests
def test_basic_rule_building(simple_html):
    """
    Test building a rule from simple HTML structure
    """
    scraper = BaseAutoScraper()
    result = scraper.build(html=simple_html, wanted_list=["Target Text"])
    
    assert len(scraper.stack_list) == 1
    rule = scraper.stack_list[0]
    
    # Verify rule structure
    assert rule["content"][-1][0] == "p"  # Last element should be paragraph
    assert rule["content"][-1][1]["class"] == "target"
    assert "Target Text" in result

def test_nested_element_rule_building(nested_html):
    """
    Test building rules from deeply nested elements
    """
    scraper = BaseAutoScraper()
    result = scraper.build(html=nested_html, wanted_list=["Nested Target"])
    
    assert len(scraper.stack_list) == 1
    rule = scraper.stack_list[0]
    
    # Verify complete hierarchy
    content = rule["content"]
    assert len(content) >= 4  # Should capture all nesting levels
    assert content[-1][0] == "span"
    assert content[-1][1]["class"] == "target"
    
    # Verify parent classes
    classes = [item[1].get("class", "") for item in content]
    assert "level1" in str(classes)
    assert "level2" in str(classes)
    assert "level3" in str(classes)

def test_multiple_rules_from_list(list_html):
    """
    Test building multiple rules from similar structures
    """
    scraper = BaseAutoScraper()
    wanted_list = ["First Item", "Second Item", "Third Item"]
    result = scraper.build(html=list_html, wanted_list=wanted_list)
    
    # Should create rules that can match all items
    assert len(result) == 3
    assert all(item in result for item in wanted_list)
    
    # Rules should share similar structure
    assert len(scraper.stack_list) >= 1
    base_rule = scraper.stack_list[0]
    assert base_rule["content"][-1][0] == "li"
    assert base_rule["content"][-1][1]["class"] == "item"

def test_regex_rule_building():
    """
    Test building rules using regular expressions
    """
    html = """
    <div>
        <span>Product123</span>
        <span>Product456</span>
        <span>Other</span>
    </div>
    """
    pattern = re.compile(r"Product\d+")
    scraper = BaseAutoScraper()
    result = scraper.build(html=html, wanted_list=[pattern])
    
    assert len(result) == 2
    assert all("Product" in item for item in result)
    assert "Other" not in result

def test_rule_updating():
    """
    Test updating existing rules with new ones
    """
    scraper = BaseAutoScraper()
    
    # First build
    html1 = "<div><p>First Target</p></div>"
    result1 = scraper.build(html=html1, wanted_list=["First Target"])
    initial_rules = len(scraper.stack_list)
    
    # Second build with update=True
    html2 = "<div><span>Second Target</span></div>"
    result2 = scraper.build(html=html2, wanted_list=["Second Target"], update=True)
    
    # Verify rules were appended
    assert len(scraper.stack_list) > initial_rules
    assert "First Target" in result1
    assert "Second Target" in result2

def test_rule_uniqueness():
    """
    Test that duplicate rules are not created
    """
    html = """
    <div>
        <p class="target">Same Text</p>
        <p class="target">Same Text</p>
    </div>
    """
    scraper = BaseAutoScraper()
    result = scraper.build(html=html, wanted_list=["Same Text"])
    
    # Should only create one rule despite multiple matches
    unique_rules = {rule["hash"] for rule in scraper.stack_list}
    assert len(unique_rules) == len(scraper.stack_list)

def test_rule_aliasing():
    """
    Test rule building with aliases
    """
    html = """
    <div>
        <span class="price">$10.99</span>
        <span class="title">Product Name</span>
    </div>
    """
    scraper = BaseAutoScraper()
    wanted_dict = {
        "price": ["$10.99"],
        "title": ["Product Name"]
    }
    result = scraper.build(html=html, wanted_dict=wanted_dict)
    
    # Verify rules have correct aliases
    aliases = {rule["alias"] for rule in scraper.stack_list}
    assert "price" in aliases
    assert "title" in aliases

def test_fuzzy_text_matching():
    """
    Test building rules with fuzzy text matching
    """
    html = """
    <div>
        <p>Almost Exact Text</p>
        <p>Almost Exact Text!</p>
        <p>Different Text</p>
    </div>
    """
    scraper = BaseAutoScraper()
    result = scraper.build(
        html=html,
        wanted_list=["Almost Exact Text"],
        text_fuzz_ratio=0.9
    )
    
    # Should match both similar texts
    assert len(result) == 2
    assert "Different Text" not in result

# Edge Cases and Error Handling

def test_empty_wanted_list():
    """
    Test behavior with empty wanted list
    """
    scraper = BaseAutoScraper()
    result = scraper.build(html="<div>Content</div>", wanted_list=[])
    assert result == []
    assert len(scraper.stack_list) == 0

def test_no_matches_found():
    """
    Test behavior when no matches are found
    """
    html = "<div>Available Text</div>"
    scraper = BaseAutoScraper()
    result = scraper.build(html=html, wanted_list=["Nonexistent Text"])
    assert result == []

def test_malformed_html_handling():
    """
    Test building rules from malformed HTML
    """
    malformed_html = """
    <div>
        <p>Text</p>
        </div>
        <p>Unclosed Tag
    """
    scraper = BaseAutoScraper()
    result = scraper.build(html=malformed_html, wanted_list=["Text"])
    assert len(result) > 0  # Should still find valid matches

def test_special_characters():
    """
    Test building rules with special characters
    """
    html = """
    <div>
        <p>Special &amp; Chars © ®</p>
        <p>Normal Text</p>
    </div>
    """
    scraper = BaseAutoScraper()
    result = scraper.build(html=html, wanted_list=["Special & Chars © ®"])
    assert "Special & Chars © ®" in result

if __name__ == "__main__":
    pytest.main([__file__])