import pytest
import aiohttp
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from aiohttp import ClientTimeout
from typing import Type, Any
from http import HTTPStatus


from development.input_layer.autoscraper_web_scraper.auto_scraper_base_class import BaseAutoScraper


class MockResponse:
    def __init__(self, text: str, status: int = 200, content_type: str = "text/html", 
                 encoding: str = "utf-8"):
        self.text = text
        self.status = status
        self._content_type = content_type
        self._encoding = encoding
        
    async def text(self) -> str:
        return self.text
        
    def get_encoding(self) -> str:
        return self._encoding
        
    @property
    def headers(self):
        return {"Content-Type": self._content_type}

class TestHTMLFetching:
    @pytest.fixture
    def scraper(self) -> Type[BaseAutoScraper]:
        """Return a concrete implementation of BaseAutoScraper for testing"""
        # Implement concrete class for testing
        class TestScraper(BaseAutoScraper):
            async def _async_fetch_html(self, url: str, request_args: dict = None) -> str:
                pass
                
            def _fetch_html(self, url: str, request_args: dict = None) -> str:
                pass
                
        return TestScraper()

    @pytest.mark.asyncio
    async def test_basic_url_fetch(self, scraper):
        """Test basic URL fetching with valid HTML response"""
        test_html = "<html><body>Test</body></html>"
        mock_response = MockResponse(test_html)
        
        with patch("aiohttp.ClientSession.get", AsyncMock(return_value=mock_response)):
            html = await scraper._async_fetch_html("http://example.com")
            assert html == test_html

    @pytest.mark.asyncio
    async def test_different_http_methods(self, scraper):
        """Test different HTTP methods (GET, POST, etc.)"""
        test_html = "<html><body>Test</body></html>"
        methods = ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"]
        
        for method in methods:
            mock_response = MockResponse(test_html)
            with patch("aiohttp.ClientSession.request", AsyncMock(return_value=mock_response)) as mock_request:
                request_args = {"method": method}
                await scraper._async_fetch_html("http://example.com", request_args)
                mock_request.assert_called_with(method, "http://example.com")

    @pytest.mark.asyncio
    async def test_custom_headers(self, scraper):
        """Test custom headers are properly passed"""
        test_headers = {
            "User-Agent": "Custom UA",
            "Accept": "text/html",
            "Authorization": "Bearer token123"
        }
        
        mock_response = MockResponse("<html></html>")
        with patch("aiohttp.ClientSession.get", AsyncMock(return_value=mock_response)) as mock_get:
            request_args = {"headers": test_headers}
            await scraper._async_fetch_html("http://example.com", request_args)
            
            # Verify headers were passed
            called_headers = mock_get.call_args[1]["headers"]
            for key, value in test_headers.items():
                assert called_headers[key] == value

    @pytest.mark.asyncio
    async def test_proxy_support(self, scraper):
        """Test proxy configuration"""
        proxy_configs = {
            "http": "http://proxy.example.com:8080",
            "https": "https://proxy.example.com:8443"
        }
        
        mock_response = MockResponse("<html></html>")
        with patch("aiohttp.ClientSession.get", AsyncMock(return_value=mock_response)) as mock_get:
            request_args = {"proxy": proxy_configs}
            await scraper._async_fetch_html("http://example.com", request_args)
            
            # Verify proxy was configured
            assert mock_get.call_args[1]["proxy"] == proxy_configs

    @pytest.mark.asyncio
    async def test_timeout_handling(self, scraper):
        """Test timeout configuration and handling"""
        timeouts = [5, 10, 30]  # seconds
        
        for timeout in timeouts:
            mock_response = MockResponse("<html></html>")
            with patch("aiohttp.ClientSession.get", AsyncMock(return_value=mock_response)) as mock_get:
                request_args = {"timeout": timeout}
                await scraper._async_fetch_html("http://example.com", request_args)
                
                # Verify timeout was set
                assert isinstance(mock_get.call_args[1]["timeout"], ClientTimeout)
                assert mock_get.call_args[1]["timeout"].total == timeout

    @pytest.mark.asyncio
    async def test_retry_logic(self, scraper):
        """Test retry behavior for failed requests"""
        test_html = "<html></html>"
        retries = 3
        
        # Mock that fails twice then succeeds
        side_effects = [
            aiohttp.ClientError(),
            aiohttp.ClientError(),
            MockResponse(test_html)
        ]
        
        with patch("aiohttp.ClientSession.get", AsyncMock(side_effect=side_effects)) as mock_get:
            request_args = {"max_retries": retries, "retry_delay": 0.1}
            html = await scraper._async_fetch_html("http://example.com", request_args)
            
            assert html == test_html
            assert mock_get.call_count == 3

    @pytest.mark.asyncio
    async def test_error_handling(self, scraper):
        """Test various error conditions"""
        error_cases = [
            # Invalid URLs
            ("not_a_url", ValueError),
            ("http://", ValueError),
            
            # Network failures
            (aiohttp.ClientError(), aiohttp.ClientError),
            (aiohttp.ServerDisconnectedError(), aiohttp.ServerDisconnectedError),
            
            # Timeout errors
            (asyncio.TimeoutError(), asyncio.TimeoutError),
            
            # HTTP errors
            (MockResponse("", status=404), aiohttp.ClientError),
            (MockResponse("", status=500), aiohttp.ClientError),
            
            # Content type errors
            (MockResponse("", content_type="application/pdf"), ValueError),
            
            # Encoding errors
            (MockResponse("", encoding="invalid"), UnicodeError)
        ]
        
        for error, expected_exception in error_cases:
            if isinstance(error, str):
                # Test invalid URLs
                with pytest.raises(expected_exception):
                    await scraper._async_fetch_html(error)
            elif isinstance(error, Exception):
                # Test network/timeout errors
                with patch("aiohttp.ClientSession.get", AsyncMock(side_effect=error)):
                    with pytest.raises(expected_exception):
                        await scraper._async_fetch_html("http://example.com")
            else:
                # Test response errors
                with patch("aiohttp.ClientSession.get", AsyncMock(return_value=error)):
                    with pytest.raises(expected_exception):
                        await scraper._async_fetch_html("http://example.com")

    @pytest.mark.asyncio
    async def test_character_encoding(self, scraper):
        """Test handling of different character encodings"""
        encodings = [
            ("utf-8", "Hello"),
            ("iso-8859-1", "Héllo"),
            ("utf-16", "Hello"),
            ("ascii", "Hello")
        ]
        
        for encoding, text in encodings:
            html = f"<html><body>{text}</body></html>".encode(encoding)
            mock_response = MockResponse(
                html.decode(encoding),
                encoding=encoding
            )
            
            with patch("aiohttp.ClientSession.get", AsyncMock(return_value=mock_response)):
                result = await scraper._async_fetch_html("http://example.com")
                assert text in result

    @pytest.mark.asyncio
    async def test_content_types(self, scraper):
        """Test handling of different content types"""
        content_types = [
            "text/html",
            "application/xhtml+xml",
            "text/plain",
            "application/xml",
            "text/xml"
        ]
        
        for content_type in content_types:
            mock_response = MockResponse(
                "<html></html>",
                content_type=content_type
            )
            
            with patch("aiohttp.ClientSession.get", AsyncMock(return_value=mock_response)):
                # Should not raise exception for valid content types
                await scraper._async_fetch_html("http://example.com")

        # Should raise for invalid content types
        invalid_types = [
            "application/pdf",
            "image/jpeg",
            "application/octet-stream"
        ]
        
        for content_type in invalid_types:
            mock_response = MockResponse(
                "<html></html>",
                content_type=content_type
            )
            
            with patch("aiohttp.ClientSession.get", AsyncMock(return_value=mock_response)):
                with pytest.raises(ValueError):
                    await scraper._async_fetch_html("http://example.com")

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, scraper):
        """Test handling multiple concurrent requests"""
        urls = [f"http://example.com/{i}" for i in range(10)]
        mock_response = MockResponse("<html></html>")
        
        with patch("aiohttp.ClientSession.get", AsyncMock(return_value=mock_response)):
            # Create tasks for concurrent execution
            tasks = [scraper._async_fetch_html(url) for url in urls]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == len(urls)
            assert all(isinstance(r, str) for r in results)

if __name__ == "__main__":
    pytest.main([__file__])