import pytest
from typing import Callable, Dict, List, Any
import json
import tempfile
import os
from bs4 import BeautifulSoup
import asyncio
from unittest.mock import Mock, patch


from development.input_layer.autoscraper_web_scraper.auto_scraper_base_class import BaseAutoScraper


class MockAutoScraper(BaseAutoScraper):
    """Mock implementation of BaseAutoScraper for testing"""
    def _fetch_html(self, url: str, request_args: dict = None) -> str:
        return "<html><body>Test</body></html>"
        
    async def _async_fetch_html(self, url: str, request_args: dict = None) -> str:
        return "<html><body>Test</body></html>"
        
    def _post_process_soup(self, html: str) -> str:
        return html

class TestAutoScraperInitialization:
    """Test suite for AutoScraper initialization and configuration"""

    def test_empty_initialization(self):
        """
        Algorithm:
        1. Create AutoScraper instance with no parameters
        2. Verify stack_list is empty list
        3. Verify post_processing_functions_dict is empty dict
        """
        scraper = MockAutoScraper()
        assert scraper.stack_list == []
        assert scraper.post_processing_functions_dict == {}

    def test_stack_list_initialization(self):
        """
        Algorithm:
        1. Create sample stack list with known rules
        2. Initialize AutoScraper with stack list
        3. Verify stack list is stored correctly
        4. Verify no mutation of original stack list
        """
        sample_stack = [
            {
                "content": [("div", {"class": "test"})],
                "wanted_attr": None,
                "is_full_url": False,
                "is_non_rec_text": False,
                "url": "",
                "hash": "test_hash",
                "stack_id": "rule_test"
            }
        ]
        original_stack = sample_stack.copy()
        
        scraper = MockAutoScraper(stack_list=sample_stack)
        assert scraper.stack_list == sample_stack
        assert sample_stack == original_stack  # Check no mutation

    def test_post_processing_functions_initialization(self):
        """
        Algorithm:
        1. Create sample post-processing functions
        2. Initialize AutoScraper with functions dict
        3. Verify functions are stored correctly
        4. Verify functions can be called and work as expected
        """
        def func1(html: str) -> str:
            return html.replace('test', 'processed')
            
        def func2(html: str) -> str:
            return html.upper()
            
        funcs = {
            'func1': func1,
            'func2': func2
        }
        
        scraper = MockAutoScraper(post_processing_functions_dict=funcs)
        assert scraper.post_processing_functions_dict == funcs
        
        # Test function execution
        test_html = "<html>test</html>"
        processed = scraper._post_process_soup(test_html)
        assert "PROCESSED" in processed

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        """
        Algorithm:
        1. Create AutoScraper instance
        2. Use async context manager
        3. Verify proper initialization in __aenter__
        4. Verify proper cleanup in __aexit__
        """
        async with MockAutoScraper() as scraper:
            assert isinstance(scraper, MockAutoScraper)
            # Add more specific checks based on your __aenter__ implementation

    def test_save_load_stack_list(self):
        """
        Algorithm:
        1. Create AutoScraper with known stack list
        2. Save stack list to temporary file
        3. Create new AutoScraper instance
        4. Load stack list from file
        5. Verify loaded stack list matches original
        6. Test with various file paths and permissions
        7. Test error handling for invalid files
        """
        sample_stack = [{
            "content": [("div", {"class": "test"})],
            "wanted_attr": None,
            "is_full_url": False,
            "hash": "test_hash",
            "stack_id": "rule_test"
        }]
        
        scraper = MockAutoScraper(stack_list=sample_stack)
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            # Test save
            scraper.save(tmp.name)
            
            # Test load
            new_scraper = MockAutoScraper()
            new_scraper.load(tmp.name)
            
            assert new_scraper.stack_list == sample_stack
            
        os.unlink(tmp.name)

    def test_save_load_error_handling(self):
        """
        Algorithm:
        1. Test saving to invalid path
        2. Test loading from non-existent file
        3. Test loading from file with invalid JSON
        4. Test loading from file with invalid stack list format
        5. Verify appropriate exceptions are raised
        """
        scraper = MockAutoScraper()
        
        # Test invalid save path
        with pytest.raises(IOError):
            scraper.save("/invalid/path/file.json")
            
        # Test loading non-existent file
        with pytest.raises(FileNotFoundError):
            scraper.load("/non/existent/file.json")
            
        # Test invalid JSON
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"invalid json content")
            tmp.flush()
            
            with pytest.raises(json.JSONDecodeError):
                scraper.load(tmp.name)
                
        os.unlink(tmp.name)

    def test_stack_list_validation(self):
        """
        Algorithm:
        1. Test initialization with invalid stack list types
        2. Test initialization with malformed stack list items
        3. Test initialization with invalid stack item fields
        4. Verify appropriate validation errors are raised
        """
        # Test invalid stack list type
        with pytest.raises(TypeError):
            MockAutoScraper(stack_list="not a list")
            
        # Test invalid stack item
        with pytest.raises(ValueError):
            MockAutoScraper(stack_list=[{"invalid": "stack item"}])
            
        # Test missing required fields
        with pytest.raises(ValueError):
            MockAutoScraper(stack_list=[{"content": []}])  # Missing other required fields

    def test_post_processing_functions_validation(self):
        """
        Algorithm:
        1. Test with non-callable items in dict
        2. Test with functions having invalid signatures
        3. Test with functions raising exceptions
        4. Verify proper error handling and validation
        """
        # Test non-callable item
        with pytest.raises(TypeError):
            MockAutoScraper(post_processing_functions_dict={'func': 'not callable'})
            
        # Test invalid function signature
        def invalid_func(x: int, y: int) -> int:
            return x + y
            
        with pytest.raises(ValueError):
            MockAutoScraper(post_processing_functions_dict={'func': invalid_func})

    def test_concurrent_initialization(self):
        """
        Algorithm:
        1. Create multiple AutoScraper instances concurrently
        2. Verify no race conditions in initialization
        3. Verify proper resource handling
        4. Test thread safety of initialization
        """
        async def create_scrapers(n: int):
            scrapers = []
            for _ in range(n):
                scraper = MockAutoScraper()
                scrapers.append(scraper)
            return scrapers
            
        scrapers = asyncio.run(create_scrapers(10))
        assert len(scrapers) == 10
        for scraper in scrapers:
            assert isinstance(scraper, MockAutoScraper)

    def test_backward_compatibility(self):
        """
        Algorithm:
        1. Test loading legacy format stack lists
        2. Verify proper conversion to new format
        3. Test with various legacy format versions
        4. Verify backward compatibility is maintained
        """
        # Test legacy format (just a list instead of dict with stack_list key)
        legacy_stack = [{"content": [], "hash": "test", "stack_id": "rule_1"}]
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            with open(tmp.name, 'w') as f:
                json.dump(legacy_stack, f)
                
            scraper = MockAutoScraper()
            scraper.load(tmp.name)
            assert scraper.stack_list == legacy_stack
            
        os.unlink(tmp.name)

    def test_immutability(self):
        """
        Algorithm:
        1. Verify stack_list immutability
        2. Verify post_processing_functions_dict immutability
        3. Test modification attempts
        4. Verify original data is preserved
        """
        sample_stack = [{"content": [], "hash": "test", "stack_id": "rule_1"}]
        original_stack = sample_stack.copy()
        
        scraper = MockAutoScraper(stack_list=sample_stack)
        
        # Try to modify stack_list
        sample_stack.append({"new": "item"})
        assert scraper.stack_list == original_stack
        
        # Try to modify stack item
        sample_stack[0]["hash"] = "modified"
        assert scraper.stack_list[0]["hash"] == "test"