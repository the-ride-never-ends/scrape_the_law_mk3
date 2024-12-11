"""
Test: Basic Context Manager
- Create scraper instance
- Enter async context
- Verify scraper is initialized
- Exit context
- Verify resources are cleaned up

Test: Context Manager Error Handling
- Create scraper instance
- Enter context
- Raise exception within context
- Verify context exits cleanly
- Verify resources are cleaned up
- Verify exception is propagated

Test: Multiple Concurrent Fetches
- Create list of 5 valid URLs
- Start concurrent fetches
- Verify all complete successfully
- Verify order of completion is not guaranteed
- Verify results are correct

Test: Mixed Success/Failure Concurrent
- Create list of URLs including valid and invalid
- Start concurrent fetches
- Verify successful fetches complete
- Verify failed fetches raise appropriate errors
- Verify partial results are returned

Test: Clean Exit Resource Check
- Create scraper with traceable resources (mock connections)
- Run operations
- Exit normally
- Verify all resources are released

Test: Error Exit Resource Check  
- Create scraper with traceable resources
- Force error during operation
- Verify all resources are released despite error

Test: Network Error During Fetch
- Setup mock server that fails intermittently
- Attempt fetch
- Verify appropriate error is raised
- Verify partial results are handled
- Verify cleanup occurs

Test: Timeout Handling
- Setup mock slow server
- Set short timeout
- Attempt fetch
- Verify timeout error is raised
- Verify cleanup occurs

Test: Task Cancellation
- Start long-running fetch
- Cancel operation mid-fetch
- Verify cancellation is clean
- Verify resources are released
- Verify no side effects remain

Test: Subtask Cancellation
- Start multiple nested async operations
- Cancel parent task
- Verify all subtasks are cancelled
- Verify all resources are released
"""


import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import AsyncIterator
import aiohttp
from aiohttp import ClientTimeout
from bs4 import BeautifulSoup
import random

from development.input_layer.autoscraper_web_scraper.auto_scraper_base_class import BaseAutoScraper
from development.input_layer.autoscraper_web_scraper.playwright_auto_scraper import PlaywrightAutoScraper


# Mock response class for testing
class MockResponse:
    def __init__(self, text: str, status: int = 200):
        self._text = text
        self.status = status
        
    async def text(self) -> str:
        return self._text
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class TestAiohttpAutoScraper:
    @pytest.fixture
    async def scraper(self) -> AsyncIterator[BaseAutoScraper]:
        """Fixture to create and cleanup scraper instance"""
        async with PlaywrightAutoScraper() as scraper:
            yield scraper

    @pytest.mark.asyncio
    async def test_basic_context_manager(self):
        """Test basic async context manager functionality"""
        resources_initialized = False
        resources_cleaned = False
        
        async with PlaywrightAutoScraper() as scraper:
            resources_initialized = scraper._browser is not None
            
        resources_cleaned = scraper._browser is None
        
        assert resources_initialized, "Resources should be initialized in context"
        assert resources_cleaned, "Resources should be cleaned up after context"

    @pytest.mark.asyncio
    async def test_context_manager_error_handling(self):
        """Test context manager handles errors properly"""
        async with pytest.raises(ValueError):
            async with PlaywrightAutoScraper() as scraper:
                assert scraper._browser is not None
                raise ValueError("Test error")
                
        assert scraper._browser is None, "Resources should be cleaned up after error"

    @pytest.mark.asyncio
    async def test_concurrent_fetches(self, scraper):
        """Test multiple concurrent fetches"""
        urls = [
            "http://example1.com",
            "http://example2.com",
            "http://example3.com",
            "http://example4.com",
            "http://example5.com"
        ]
        
        mock_html = "<html><body>Test</body></html>"
        
        async def mock_fetch(url):
            await asyncio.sleep(random.random())  # Simulate varying response times
            return mock_html
            
        with patch.object(scraper, '_fetch_html', side_effect=mock_fetch):
            # Start all fetches concurrently
            tasks = [scraper._fetch_html(url) for url in urls]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == len(urls)
            assert all(r == mock_html for r in results)

    @pytest.mark.asyncio
    async def test_mixed_success_failure_concurrent(self, scraper):
        """Test concurrent fetches with mixed success/failure"""
        urls = [
            "http://success1.com",
            "http://fail1.com",
            "http://success2.com",
            "http://fail2.com",
        ]
        
        async def mock_fetch(url):
            await asyncio.sleep(random.random())
            if 'fail' in url:
                raise aiohttp.ClientError("Failed fetch")
            return "<html><body>Success</body></html>"
            
        with patch.object(scraper, '_fetch_html', side_effect=mock_fetch):
            tasks = [scraper._fetch_html(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successes = [r for r in results if isinstance(r, str)]
            failures = [r for r in results if isinstance(r, Exception)]
            
            assert len(successes) == 2
            assert len(failures) == 2

    @pytest.mark.asyncio
    async def test_resource_cleanup(self, scraper):
        """Test proper resource cleanup"""
        mock_resources = []
        
        class MockResource:
            def __init__(self):
                self.closed = False
                mock_resources.append(self)
                
            async def close(self):
                self.closed = True
                
        # Patch resource creation
        with patch.object(scraper, '_create_resource', return_value=MockResource()):
            await scraper._fetch_html("http://example.com")
            
        # Verify all resources are closed
        assert all(r.closed for r in mock_resources)

    @pytest.mark.asyncio
    async def test_error_resource_cleanup(self, scraper):
        """Test resource cleanup after error"""
        mock_resources = []
        
        class MockResource:
            def __init__(self):
                self.closed = False
                mock_resources.append(self)
                
            async def close(self):
                self.closed = True
                
        with patch.object(scraper, '_create_resource', return_value=MockResource()):
            with pytest.raises(ValueError):
                await scraper._fetch_html("http://example.com")
                raise ValueError("Test error")
                
        assert all(r.closed for r in mock_resources)

    @pytest.mark.asyncio
    async def test_network_error_handling(self, scraper):
        """Test handling of network errors"""
        failed_count = 0
        
        async def failing_fetch(url):
            nonlocal failed_count
            failed_count += 1
            if failed_count % 2 == 0:
                raise aiohttp.ClientError("Network error")
            return "<html><body>Success</body></html>"
            
        with patch.object(scraper, '_fetch_html', side_effect=failing_fetch):
            with pytest.raises(aiohttp.ClientError):
                await scraper._fetch_html("http://example.com")
                
            # Verify retry mechanism
            result = await scraper._fetch_html("http://example.com")
            assert "Success" in result

    @pytest.mark.asyncio
    async def test_timeout_handling(self, scraper):
        """Test timeout handling"""
        async def slow_fetch(url):
            await asyncio.sleep(2)
            return "<html><body>Too late</body></html>"
            
        with patch.object(scraper, '_fetch_html', side_effect=slow_fetch):
            with pytest.raises(asyncio.TimeoutError):
                async with asyncio.wait_for(0.1):
                    await scraper._fetch_html("http://example.com")

    @pytest.mark.asyncio
    async def test_task_cancellation(self, scraper):
        """Test handling of task cancellation"""
        cancel_called = False
        
        async def cancelable_fetch(url):
            nonlocal cancel_called
            try:
                await asyncio.sleep(10)
                return "<html><body>Should not reach</body></html>"
            except asyncio.CancelledError:
                cancel_called = True
                raise
                
        with patch.object(scraper, '_fetch_html', side_effect=cancelable_fetch):
            task = asyncio.create_task(scraper._fetch_html("http://example.com"))
            await asyncio.sleep(0.1)
            task.cancel()
            
            with pytest.raises(asyncio.CancelledError):
                await task
                
            assert cancel_called, "Cancellation handler should be called"

    @pytest.mark.asyncio
    async def test_subtask_cancellation(self, scraper):
        """Test cancellation of nested tasks"""
        subtasks_cancelled = []
        
        async def nested_operation():
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                subtasks_cancelled.append(True)
                raise
                
        async def main_operation():
            tasks = [asyncio.create_task(nested_operation()) for _ in range(3)]
            try:
                await asyncio.gather(*tasks)
            except asyncio.CancelledError:
                # Ensure subtasks are cancelled
                for task in tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                raise
                
        task = asyncio.create_task(main_operation())
        await asyncio.sleep(0.1)
        task.cancel()
        
        with pytest.raises(asyncio.CancelledError):
            await task
            
        assert len(subtasks_cancelled) == 3, "All subtasks should be cancelled"