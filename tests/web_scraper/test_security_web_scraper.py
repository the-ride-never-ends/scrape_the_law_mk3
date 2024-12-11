"""
Security Test Suite for AutoScraper
---------------------------------

1. XSS Testing Algorithms:
   - Test reflected XSS: Create HTML with script tags in various contexts
   - Test stored XSS: Ensure script content isn't executed when parsed
   - Test DOM-based XSS: Check handling of dynamic content
   - Test XSS in attributes: Verify script in attributes isn't executed
   - Test XSS in different contexts (comments, CDATA, etc)

2. CSRF Testing:
   - Test token handling
   - Test origin validation
   - Test referrer validation
   - Test custom header requirements

3. Content Injection:
   - Test HTML injection
   - Test JavaScript injection
   - Test CSS injection
   - Test iframe injection
   - Test meta refresh injection

4. Protocol Handler Testing:
   - Test http/https validation
   - Test file:// protocol blocking
   - Test data:// protocol blocking
   - Test javascript:// protocol blocking
   - Test custom protocol handling

5. Resource Access Testing:
   - Test file path traversal
   - Test URL path traversal
   - Test access to local resources
   - Test access to network resources
   - Test access to system resources

6. Input Validation:
   - Test URL validation
   - Test header validation
   - Test content validation
   - Test encoding validation
   - Test size limits
"""

import pytest
import aiohttp
import asyncio
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup
from unittest.mock import Mock, patch
from urllib.parse import urljoin

from development.input_layer.autoscraper_web_scraper.auto_scraper_base_class import BaseAutoScraper
from development.input_layer.autoscraper_web_scraper.aiohttp_auto_scraper import AiohttpAutoScraper
from development.input_layer.autoscraper_web_scraper.playwright_auto_scraper import PlaywrightAutoScraper


# Mock server for testing
class MockServer:
    def __init__(self):
        self.app = aiohttp.web.Application()
        self.app.router.add_get('/', self.handle_get)
        self.runner = None

    async def start(self):
        self.runner = aiohttp.web.AppRunner(self.app)
        await self.runner.setup()
        site = aiohttp.web.TCPSite(self.runner, 'localhost', 8080)
        await site.start()

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()

    async def handle_get(self, request):
        return aiohttp.web.Response(text="Test response")

# Test fixtures
@pytest.fixture
async def mock_server():
    server = MockServer()
    await server.start()
    yield server
    await server.stop()

@pytest.fixture
def scraper():
    return AiohttpAutoScraper()

# 1. XSS Testing
class TestXSSSecurity:
    @pytest.mark.asyncio
    async def test_reflected_xss(self, scraper):
        """
        Test handling of script tags in HTML content
        """
        malicious_html = """
        <html>
            <body>
                <script>alert('xss')</script>
                <div>Normal content</div>
            </body>
        </html>
        """
        soup = BeautifulSoup(malicious_html, 'lxml')
        result = await scraper._process_soup(malicious_html)
        
        # Verify script tags are not executed but still preserved in the DOM
        assert 'script' in str(result)
        assert not any(tag.string == "alert('xss')" for tag in result.find_all('script'))

    @pytest.mark.asyncio
    async def test_dom_xss(self, scraper):
        """
        Test handling of dynamic content that might contain XSS
        """
        malicious_html = """
        <html>
            <body>
                <div id="content"></div>
                <script>
                    document.getElementById('content').innerHTML = '<img src=x onerror=alert(1)>';
                </script>
            </body>
        </html>
        """
        result = await scraper._process_soup(malicious_html)
        
        # Verify event handlers are stripped
        assert 'onerror' not in str(result)

    @pytest.mark.asyncio
    async def test_attribute_xss(self, scraper):
        """
        Test handling of XSS in HTML attributes
        """
        malicious_html = """
        <html>
            <body>
                <img src="x" onerror="alert(1)">
                <a href="javascript:alert(1)">Click me</a>
            </body>
        </html>
        """
        result = await scraper._process_soup(malicious_html)
        
        # Verify dangerous attributes and protocols are removed
        assert 'javascript:' not in str(result)
        assert 'onerror' not in str(result)

# 2. CSRF Testing
class TestCSRFSecurity:
    @pytest.mark.asyncio
    async def test_csrf_token_handling(self, scraper):
        """
        Test proper handling of CSRF tokens in requests
        """
        headers = {'X-CSRF-Token': 'test-token'}
        
        with patch.object(scraper, '_fetch_html') as mock_fetch:
            await scraper._async_fetch_html('http://example.com', {'headers': headers})
            mock_fetch.assert_called_with('http://example.com', {'headers': headers})

    @pytest.mark.asyncio
    async def test_origin_validation(self, scraper):
        """
        Test validation of origin headers
        """
        headers = {'Origin': 'http://malicious.com'}
        
        with pytest.raises(ValueError):
            await scraper._async_fetch_html('http://example.com', {'headers': headers})

# 3. Content Injection Tests
class TestContentInjection:
    @pytest.mark.asyncio
    async def test_html_injection(self, scraper):
        """
        Test handling of injected HTML content
        """
        malicious_html = """
        <html>
            <body>
                <div>Normal content</div>
                <!-- inject-start -->
                <script>alert(1)</script>
                <!-- inject-end -->
            </body>
        </html>
        """
        result = await scraper._process_soup(malicious_html)
        
        # Verify injected content is properly sanitized
        assert '<!-- inject-start -->' in str(result)
        assert '<script>' not in str(result)

    @pytest.mark.asyncio
    async def test_iframe_injection(self, scraper):
        """
        Test handling of iframe injection attempts
        """
        malicious_html = """
        <html>
            <body>
                <iframe src="javascript:alert(1)"></iframe>
                <iframe src="file:///etc/passwd"></iframe>
            </body>
        </html>
        """
        result = await scraper._process_soup(malicious_html)
        
        # Verify dangerous iframe sources are removed
        iframes = result.find_all('iframe')
        for iframe in iframes:
            assert 'javascript:' not in iframe.get('src', '')
            assert 'file://' not in iframe.get('src', '')

# 4. Protocol Handler Tests
class TestProtocolSecurity:
    @pytest.mark.asyncio
    async def test_protocol_validation(self, scraper):
        """
        Test validation of URL protocols
        """
        dangerous_protocols = [
            'file:///etc/passwd',
            'data:text/html,<script>alert(1)</script>',
            'javascript:alert(1)',
            'ftp://example.com'
        ]
        
        for url in dangerous_protocols:
            with pytest.raises(ValueError):
                await scraper._async_fetch_html(url)

    @pytest.mark.asyncio
    async def test_https_downgrade(self, scraper):
        """
        Test prevention of HTTPS to HTTP downgrade
        """
        https_url = 'https://example.com'
        http_redirect = 'http://example.com'
        
        with pytest.raises(ValueError):
            # Simulate a redirect to HTTP
            with patch.object(scraper, '_async_fetch_html') as mock_fetch:
                mock_fetch.return_value = http_redirect
                await scraper._async_fetch_html(https_url)

# 5. Resource Access Tests
class TestResourceAccess:
    @pytest.mark.asyncio
    async def test_path_traversal(self, scraper):
        """
        Test prevention of path traversal attempts
        """
        dangerous_paths = [
            'http://example.com/../../../etc/passwd',
            'http://example.com/folder/../../secret',
            'http://example.com/%2e%2e%2f%2e%2e%2f'
        ]
        
        for url in dangerous_paths:
            with pytest.raises(ValueError):
                await scraper._async_fetch_html(url)

    @pytest.mark.asyncio
    async def test_local_resource_access(self, scraper):
        """
        Test prevention of local resource access
        """
        local_urls = [
            'http://localhost/secret',
            'http://127.0.0.1/admin',
            'http://0.0.0.0/config'
        ]
        
        for url in local_urls:
            with pytest.raises(ValueError):
                await scraper._async_fetch_html(url)

# 6. Input Validation Tests
class TestInputValidation:
    @pytest.mark.asyncio
    async def test_url_validation(self, scraper):
        """
        Test validation of URLs
        """
        invalid_urls = [
            'not-a-url',
            'http://',
            'https://',
            'http://a',
            'http:///example.com'
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValueError):
                await scraper._async_fetch_html(url)

    @pytest.mark.asyncio
    async def test_header_validation(self, scraper):
        """
        Test validation of HTTP headers
        """
        dangerous_headers = {
            'Host': 'malicious.com',
            'X-Forwarded-For': '127.0.0.1',
            'Cookie': 'session=admin'
        }
        
        with pytest.raises(ValueError):
            await scraper._async_fetch_html('http://example.com', 
                                          {'headers': dangerous_headers})

    @pytest.mark.asyncio
    async def test_content_size_limits(self, scraper):
        """
        Test enforcement of content size limits
        """
        large_content = 'a' * (10 * 1024 * 1024)  # 10MB
        
        with pytest.raises(ValueError):
            await scraper._process_soup(large_content)