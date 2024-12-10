"""
Test Algorithms:

1. Basic HTML Parsing
- Input valid HTML with basic elements
- Verify correct tree structure is created
- Check element attributes are preserved
- Verify text content is correctly extracted

2. Character Encoding Tests
- Test UTF-8 encoded content
- Test ISO-8859-1 encoded content
- Test HTML with specified vs detected encoding
- Test mixed encoding scenarios
- Test invalid encoding handling

3. Post-Processing Function Tests
- Test single post-processing function
- Test multiple functions in sequence
- Test function ordering
- Test function error handling
- Test function modification of content

4. BeautifulSoup Object Creation
- Test parser selection (lxml)
- Test parser options
- Test invalid HTML recovery
- Test partial HTML handling

5. HTML Normalization
- Test whitespace handling
- Test line ending normalization
- Test tag case normalization
- Test attribute normalization

6. HTML Unescaping
- Test basic HTML entities
- Test numeric entities
- Test custom entities
- Test mixed escaped/unescaped content

7. Invalid HTML Handling
- Test unclosed tags
- Test mismatched tags
- Test invalid attributes
- Test malformed DOCTYPE
- Test incomplete HTML
"""

import pytest
from bs4 import BeautifulSoup
from html import unescape
import codecs
from typing import Callable, Dict, List


from development.input_layer.autoscraper_web_scraper.auto_scraper_base_class import BaseAutoScraper


class MockAutoScraper(BaseAutoScraper):
    """Mock class for testing"""
    def _fetch_html(self, url, request_args=None):
        return "<html><body>Test</body></html>"
        
    async def _async_fetch_html(self, url, request_args=None):
        return "<html><body>Test</body></html>"

# 1. Basic HTML Parsing Tests
def test_basic_html_parsing():
    scraper = MockAutoScraper()
    html = """
    <html>
        <body>
            <div class="test" id="main">
                <p>Hello World</p>
            </div>
        </body>
    </html>
    """
    soup = scraper._process_soup(html)
    
    assert isinstance(soup, BeautifulSoup)
    assert soup.find('div')['class'] == ['test']
    assert soup.find('p').text.strip() == 'Hello World'

def test_nested_structure_parsing():
    scraper = MockAutoScraper()
    html = """
    <div>
        <ul>
            <li>Item 1</li>
            <li>Item 2
                <ul>
                    <li>Subitem 1</li>
                </ul>
            </li>
        </ul>
    </div>
    """
    soup = scraper._process_soup(html)
    items = soup.find_all('li')
    assert len(items) == 3
    assert items[0].text.strip() == 'Item 1'

# 2. Character Encoding Tests
def test_utf8_encoding():
    scraper = MockAutoScraper()
    html = '<p>Hello 世界</p>'.encode('utf-8').decode('utf-8')
    soup = scraper._process_soup(html)
    assert soup.find('p').text == 'Hello 世界'

def test_iso_8859_1_encoding():
    scraper = MockAutoScraper()
    html = '<p>Hello é</p>'.encode('iso-8859-1').decode('iso-8859-1')
    soup = scraper._process_soup(html)
    assert soup.find('p').text == 'Hello é'

def test_mixed_encoding():
    scraper = MockAutoScraper()
    html = '<!DOCTYPE html><meta charset="utf-8"><p>Hello 世界 é</p>'
    soup = scraper._process_soup(html)
    assert soup.find('p').text == 'Hello 世界 é'

# 3. Post-Processing Function Tests
def test_single_post_processing():
    def uppercase_text(html: str) -> str:
        return html.upper()
        
    scraper = MockAutoScraper(
        post_processing_functions_dict={'uppercase': uppercase_text}
    )
    html = '<p>hello world</p>'
    soup = scraper._process_soup(html)
    assert soup.find('p').text == 'HELLO WORLD'

def test_multiple_post_processing():
    def add_prefix(html: str) -> str:
        return html.replace('<p>', '<p>PREFIX: ')
        
    def add_suffix(html: str) -> str:
        return html.replace('</p>', ' :SUFFIX</p>')
        
    scraper = MockAutoScraper(
        post_processing_functions_dict={
            'prefix': add_prefix,
            'suffix': add_suffix
        }
    )
    html = '<p>test</p>'
    soup = scraper._process_soup(html)
    assert soup.find('p').text == 'PREFIX: test :SUFFIX'

def test_post_processing_error():
    def faulty_processor(html: str) -> str:
        raise ValueError("Processing error")
        
    scraper = MockAutoScraper(
        post_processing_functions_dict={'faulty': faulty_processor}
    )
    html = '<p>test</p>'
    with pytest.raises(ValueError):
        scraper._process_soup(html)

# 4. BeautifulSoup Object Creation Tests
def test_partial_html():
    scraper = MockAutoScraper()
    html = '<div>Test</div>'  # No full HTML structure
    soup = scraper._process_soup(html)
    assert soup.find('div').text == 'Test'

def test_invalid_html_recovery():
    scraper = MockAutoScraper()
    html = '<p>Test<p>More test</p>'  # Unclosed p tag
    soup = scraper._process_soup(html)
    paragraphs = soup.find_all('p')
    assert len(paragraphs) == 2
    assert paragraphs[0].text == 'Test'

# 5. HTML Normalization Tests
def test_whitespace_normalization():
    scraper = MockAutoScraper()
    html = '<p>  Hello    World\n\t</p>'
    soup = scraper._process_soup(html)
    assert soup.find('p').text.strip() == 'Hello World'

def test_attribute_normalization():
    scraper = MockAutoScraper()
    html = '<div  CLASS="test"   ID="main"  >Test</div>'
    soup = scraper._process_soup(html)
    div = soup.find('div')
    assert div['class'] == ['test']
    assert div['id'] == 'main'

# 6. HTML Unescaping Tests
def test_basic_entity_unescaping():
    scraper = MockAutoScraper()
    html = '<p>&lt;Hello&gt; &amp; World</p>'
    soup = scraper._process_soup(html)
    assert soup.find('p').text == '<Hello> & World'

def test_numeric_entity_unescaping():
    scraper = MockAutoScraper()
    html = '<p>&#72;&#101;&#108;&#108;&#111;</p>'
    soup = scraper._process_soup(html)
    assert soup.find('p').text == 'Hello'

# 7. Invalid HTML Handling Tests
def test_mismatched_tags():
    scraper = MockAutoScraper()
    html = '<div><p>Test</div></p>'
    soup = scraper._process_soup(html)
    assert soup.find('p').text == 'Test'

def test_invalid_attributes():
    scraper = MockAutoScraper()
    html = '<div class=test" id="main">Test</div>'
    soup = scraper._process_soup(html)
    assert soup.find('div').text == 'Test'

def test_incomplete_html():
    scraper = MockAutoScraper()
    html = '<div>Test'
    soup = scraper._process_soup(html)
    assert soup.find('div').text == 'Test'

# Helper functions for testing
def compare_html_structure(soup1: BeautifulSoup, soup2: BeautifulSoup) -> bool:
    """Compare two BeautifulSoup objects for structural equality"""
    if soup1.name != soup2.name:
        return False
    if soup1.string != soup2.string:
        return False
    if len(soup1.contents) != len(soup2.contents):
        return False
    return all(compare_html_structure(c1, c2) 
              for c1, c2 in zip(soup1.contents, soup2.contents))

def create_mock_processor(transform_func: Callable[[str], str]) -> Callable[[str], str]:
    """Create a mock post-processing function with the given transform"""
    def processor(html: str) -> str:
        try:
            return transform_func(html)
        except Exception as e:
            raise ValueError(f"Processing error: {str(e)}")
    return processor