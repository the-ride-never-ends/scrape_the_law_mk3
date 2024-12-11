import aiohttp
import asyncio
import os
from typing import Any, Callable, Coroutine, Optional, OrderedDict, TypeVar, Union
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser


from bs4 import BeautifulSoup, PageElement, Tag, ResultSet
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, PlaywrightContextManager, Playwright


from utils.shared.make_id import make_id

from development.input_layer.autoscraper_web_scraper.auto_scraper_base_class import BaseAutoScraper


T = TypeVar('T')


class Trigger():
    stack_list: OrderedDict = {}


class PlaywrightTrigger(Trigger):
    playwright_stack_list: list[Callable|Coroutine] = []


class PlaywrightAutoScraper(BaseAutoScraper):
    """
    AutoScraper implementation using Playwright for JavaScript-rendered content
    """
    
    def __init__(self, 
                 stack_list=None, 
                 browser_type: str = "chromium", 
                 post_processing: dict = None,
                 id: int = None
                ):
        super().__init__(stack_list=stack_list, post_processing=post_processing)
        self.browser_type: Browser = browser_type
        self._playwright: Playwright = None
        self._browser: Browser = None

    async def enter(self) -> None:
        self._playwright = await async_playwright().start()
        browser_launch = getattr(self._playwright, self.browser_type)
        self._browser = await browser_launch.launch()


    async def exit_(self, exc_type, exc_val, exc_tb) -> None:
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()


    async def __aenter__(self):
        await self.enter()
        return self


    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return await self.exit_(exc_type, exc_val, exc_tb)


    async def _fetch_html(self, url: str, request_args: Optional[dict[str, Any]] = None) -> str:
        if not self._browser:
            raise RuntimeError("Browser not initialized. Use 'async with' context manager.")

        request_args = request_args or {}
        page = await self._browser.new_page()

        try:
            # Handle any Playwright-specific options from request_args
            wait_until = request_args.get('wait_until', 'networkidle')
            timeout = request_args.get('timeout', 30000)

            await page.goto(url, wait_until=wait_until, timeout=timeout)

            html = await page.content()
            return html
        finally:
            await page.close()



