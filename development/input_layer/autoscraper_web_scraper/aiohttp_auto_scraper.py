


from abc import ABC, abstractmethod
import aiohttp
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, PlaywrightContextManager, Playwright

from collections import defaultdict

from bs4 import BeautifulSoup
from urllib.parse import urlparse
import asyncio
from typing import Optional, Dict, Any, Union
import os


from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlsplit, urlparse


from logger.logger import Logger


from auto_scraper_base_class import BaseAutoScraper

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 \
        (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36",
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}


class AiohttpAutoScraper(BaseAutoScraper):
    """AutoScraper implementation using aiohttp for basic requests"""

    async def _fetch_html(self, url: str, request_args: Optional[Dict[str, Any]] = None) -> str:
        request_args = request_args or {}
        headers = dict(REQUEST_HEADERS)
        if url:
            headers["Host"] = urlparse(url).netloc

        user_headers = request_args.pop("headers", {})
        headers.update(user_headers)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, **request_args) as response:
                html = await response.text()
                
                # Handle encoding similar to requests
                if response.get_encoding() == "ISO-8859-1" and \
                   "ISO-8859-1" not in response.headers.get("Content-Type", ""):
                    # Note: aiohttp doesn't have apparent_encoding, we might need to implement
                    # a similar functionality or use chardet
                    pass
                    
                return html


# Factory function to create appropriate scraper based on needs
def create_scraper(scraper_type: str = "async", **kwargs) -> BaseAutoScraper:
    """
    Factory function to create the appropriate type of scraper
    
    Args:
        scraper_type: One of "async" (aiohttp) or "playwright"
        **kwargs: Additional arguments passed to the scraper constructor
    
    Returns:
        BaseAutoScraper: An instance of the appropriate scraper class

    Example:
    ```
        async def example_usage():
            # Basic async scraping
            async_scraper = create_scraper("async")
            results = await async_scraper.build(url="http://example.com", wanted_list=["Example Domain"])
            
            # JavaScript-rendered content
            async with create_scraper("playwright") as playwright_scraper:
                results = await playwright_scraper.build(
                    url="http://example.com", 
                    wanted_list=["Example Domain"]
                )
    """
    scrapers = {
        "requests": RequestsAutoScraper,
        "aiohttp": AiohttpAutoScraper,
        "playwright": PlaywrightAutoScraper
    }
    
    if scraper_type not in scrapers:
        raise ValueError(f"Invalid scraper_type. Must be one of: {', '.join(scrapers.keys())}")
        
    return scrapers[scraper_type](**kwargs)


