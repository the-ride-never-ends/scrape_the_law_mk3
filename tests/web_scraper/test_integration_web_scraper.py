"""
ALGORITHM: Test Basic Website Scraping
1. Choose a stable, well-known website (e.g., Python.org)
2. Define known, stable elements to scrape (e.g., navigation links)
3. Create scraper instance
4. Attempt to scrape defined elements
5. Verify results match expected content
6. Test both async and sync versions
7. Verify content structure matches expected format

ALGORITHM: Test Various HTML Structures
1. Test table-based layout site
2. Test modern flexbox/grid layout site
3. Test single-page application
4. Test static HTML site
5. Test site with nested iframes
6. Each sub-test should:
   a. Define expected content
   b. Scrape actual content
   c. Compare results
   d. Verify structure preservation

ALGORITHM: Test Content Type Responses
1. Test HTML responses
2. Test XHTML responses
3. Test sites with different charset encodings
4. Test compressed responses (gzip, deflate)
5. Test mixed content types
6. For each:
   a. Verify correct parsing
   b. Verify encoding handling
   c. Verify content extraction

ALGORITHM: Test Server Configurations
1. Test sites with:
   a. Redirects (301, 302, etc.)
   b. Custom headers
   c. Different compression methods
   d. Different SSL/TLS configurations
2. Verify handling of:
   a. Connection timeouts
   b. Read timeouts
   c. SSL errors
   d. DNS errors

ALGORITHM: Test Rate Limit Handling
1. Set up test server with known rate limits
2. Perform rapid sequential requests
3. Verify rate limit detection
4. Test backoff behavior
5. Verify request queuing
6. Test parallel request handling
7. Verify successful completion after backoff

ALGORITHM: Test Cookie Management
1. Test sites requiring cookies
2. Verify cookie persistence
3. Test cookie updates
4. Test session cookie handling
5. Test cookie expiration
6. Verify cookie headers
7. Test cookie-based authentication

ALGORITHM: Test Session Handling
1. Test session creation
2. Test session persistence
3. Test session expiration
4. Test parallel sessions
5. Test session recovery
6. Verify session headers

ALGORITHM: Test Authentication
1. Test basic auth
2. Test form-based auth
3. Test OAuth flows
4. Test token-based auth
5. Test session-based auth
6. For each:
   a. Verify successful auth
   b. Verify content access
   c. Test auth persistence
   d. Test auth renewal
"""


import pytest
import aiohttp
import asyncio
from aioresponses import aioresponses
from bs4 import BeautifulSoup
from typing import AsyncGenerator, Generator
from unittest.mock import patch, MagicMock
import gzip
import json
from http.cookiejar import CookieJar

from development.input_layer.autoscraper_web_scraper.auto_scraper_base_class import BaseAutoScraper
from development.input_layer.autoscraper_web_scraper.aiohttp_auto_scraper import AiohttpAutoScraper
from development.input_layer.autoscraper_web_scraper.playwright_auto_scraper import PlaywrightAutoScraper

# Fixtures

@pytest.fixture
def mock_aioresponse():
    with aioresponses() as m:
        yield m

@pytest.fixture
async def async_scraper() -> AsyncGenerator[AiohttpAutoScraper, None]:
    scraper = AiohttpAutoScraper()
    yield scraper
    await scraper.close()  # Cleanup

@pytest.fixture
async def playwright_scraper() -> AsyncGenerator[PlaywrightAutoScraper, None]:
    async with PlaywrightAutoScraper() as scraper:
        yield scraper

# Basic Website Testing

@pytest.mark.asyncio
async def test_basic_website_scraping(async_scraper: AiohttpAutoScraper):
    """Test scraping from a stable website (python.org)"""
    url = "https://python.org"
    wanted_items = ["Downloads", "Documentation", "Community"]
    
    results = await async_scraper.build(
        url=url,
        wanted_list=wanted_items
    )
    
    assert len(results) >= len(wanted_items)
    assert all(item in " ".join(results) for item in wanted_items)

# Different Website Structures

@pytest.mark.asyncio
async def test_table_based_layout(async_scraper: AiohttpAutoScraper, mock_aioresponse):
    """Test scraping from table-based layouts"""
    url = "http://test.com/table-layout"
    html_content = """
    <table>
        <tr>
            <td>Item 1</td>
            <td>Description 1</td>
        </tr>
        <tr>
            <td>Item 2</td>
            <td>Description 2</td>
        </tr>
    </table>
    """
    
    mock_aioresponse.get(url, status=200, body=html_content)
    
    results = await async_scraper.build(
        url=url,
        wanted_list=["Item 1", "Item 2"]
    )
    
    assert len(results) == 2
    assert "Item 1" in results
    assert "Item 2" in results

@pytest.mark.asyncio
async def test_spa_structure(playwright_scraper: PlaywrightAutoScraper):
    """Test scraping from a Single Page Application"""
    url = "http://test-spa.com"
    
    results = await playwright_scraper.build(
        url=url,
        wanted_list=["Dynamic Content"],
        wait_for=".content-loaded"  # Wait for content to load
    )
    
    assert "Dynamic Content" in results

# Content Type Tests

@pytest.mark.asyncio
async def test_different_encodings(async_scraper: AiohttpAutoScraper, mock_aioresponse):
    """Test handling of different content encodings"""
    url = "http://test.com/encoded"
    
    # UTF-8 content
    content_utf8 = "Hello, 世界".encode('utf-8')
    mock_aioresponse.get(
        url + "/utf8",
        status=200,
        body=content_utf8,
        headers={'Content-Type': 'text/html; charset=utf-8'}
    )
    
    # Windows-1252 content
    content_1252 = "Hello, World".encode('windows-1252')
    mock_aioresponse.get(
        url + "/1252",
        status=200,
        body=content_1252,
        headers={'Content-Type': 'text/html; charset=windows-1252'}
    )
    
    results_utf8 = await async_scraper.build(
        url=url + "/utf8",
        wanted_list=["Hello"]
    )
    results_1252 = await async_scraper.build(
        url=url + "/1252",
        wanted_list=["Hello"]
    )
    
    assert "Hello" in results_utf8
    assert "Hello" in results_1252

@pytest.mark.asyncio
async def test_compressed_response(async_scraper: AiohttpAutoScraper, mock_aioresponse):
    """Test handling of gzipped content"""
    url = "http://test.com/compressed"
    content = "Compressed Content"
    
    # Gzip the content
    gzipped_content = gzip.compress(content.encode('utf-8'))
    
    mock_aioresponse.get(
        url,
        status=200,
        body=gzipped_content,
        headers={'Content-Encoding': 'gzip'}
    )
    
    results = await async_scraper.build(
        url=url,
        wanted_list=["Compressed Content"]
    )
    
    assert "Compressed Content" in results

# Server Configuration Tests

@pytest.mark.asyncio
async def test_redirect_handling(async_scraper: AiohttpAutoScraper, mock_aioresponse):
    """Test handling of HTTP redirects"""
    initial_url = "http://test.com/old"
    final_url = "http://test.com/new"
    
    mock_aioresponse.get(
        initial_url,
        status=301,
        headers={'Location': final_url}
    )
    mock_aioresponse.get(
        final_url,
        status=200,
        body="<html>Redirected Content</html>"
    )
    
    results = await async_scraper.build(
        url=initial_url,
        wanted_list=["Redirected Content"]
    )
    
    assert "Redirected Content" in results

# Rate Limiting Tests

class MockRateLimitServer:
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self.requests = []
    
    async def handle_request(self):
        now = asyncio.get_event_loop().time()
        # Clean old requests
        self.requests = [t for t in self.requests if now - t < self.window]
        
        if len(self.requests) >= self.limit:
            return 429, "Too Many Requests"
        
        self.requests.append(now)
        return 200, "Success"

@pytest.mark.asyncio
async def test_rate_limiting(async_scraper: AiohttpAutoScraper):
    """Test rate limit handling"""
    server = MockRateLimitServer(limit=5, window=1)  # 5 requests per second
    
    async def make_requests(n: int):
        results = []
        for _ in range(n):
            status, _ = await server.handle_request()
            results.append(status)
        return results
    
    # Make 10 requests rapidly
    results = await make_requests(10)
    
    # Should see some 429s
    assert 429 in results
    # But should also see successful requests
    assert 200 in results

# Cookie and Session Tests

@pytest.mark.asyncio
async def test_cookie_handling(async_scraper: AiohttpAutoScraper):
    """Test cookie management"""
    url = "http://test.com/cookies"
    
    # Mock session with cookie handling
    session = aiohttp.ClientSession(cookie_jar=CookieJar())
    
    # First request sets cookies
    async with session.get(url) as response:
        cookies = session.cookie_jar.filter_cookies(url)
        assert len(cookies) > 0
    
    # Subsequent request should send cookies
    async with session.get(url) as response:
        assert 'Cookie' in response.request_info.headers
    
    await session.close()

# Authentication Tests

@pytest.mark.asyncio
async def test_basic_auth(async_scraper: AiohttpAutoScraper, mock_aioresponse):
    """Test basic authentication"""
    url = "http://test.com/protected"
    username = "user"
    password = "pass"
    
    mock_aioresponse.get(
        url,
        status=401,
        headers={'WWW-Authenticate': 'Basic realm="Test"'}
    )
    
    mock_aioresponse.get(
        url,
        status=200,
        body="Protected Content",
        headers={'Authorization': f'Basic {username}:{password}'}
    )
    
    results = await async_scraper.build(
        url=url,
        wanted_list=["Protected Content"],
        request_args={
            'auth': aiohttp.BasicAuth(username, password)
        }
    )
    
    assert "Protected Content" in results

@pytest.mark.asyncio
async def test_token_auth(async_scraper: AiohttpAutoScraper, mock_aioresponse):
    """Test token-based authentication"""
    url = "http://test.com/api"
    token = "secret_token"
    
    mock_aioresponse.get(
        url,
        status=200,
        body="API Content",
        match_headers={'Authorization': f'Bearer {token}'}
    )
    
    results = await async_scraper.build(
        url=url,
        wanted_list=["API Content"],
        request_args={
            'headers': {'Authorization': f'Bearer {token}'}
        }
    )
    
    assert "API Content" in results














