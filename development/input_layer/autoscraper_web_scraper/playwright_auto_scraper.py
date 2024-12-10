import aiohttp
import asyncio
import os
from typing import Any, Optional, TypeVar
from urllib.parse import urljoin,
from urllib.pare


from bs4 import BeautifulSoup, PageElement, Tag, ResultSet
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, PlaywrightContextManager, Playwright


from utils.shared.make_id import make_id
from logger.logger import Logger

from development.input_layer.autoscraper_web_scraper.auto_scraper_base_class import BaseAutoScraper


T = TypeVar('T')

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
        self.logger: Logger = Logger(logger_name=f"{self.__qualname__}__{str(id)}")


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


    # Define class enter and exit methods.
    async def get_robot_rules(self) -> None:
        """
        Get the site's robots.txt file and read it asynchronously with a timeout.
        TODO Make a database of robots.txt files. This might be a good idea for scraping.
        """
        robots_url = urljoin(self.domain, 'robots.txt')

        # Check if we already got the robots.txt file for this website
        robots_txt_filepath = self.robots_txt_filepath
        e_tuple: tuple = None

        self.rp = RobotFileParser(robots_url)

        # If we already got the robots.txt file, load it in.
        if os.path.exists(self.robots_txt_filepath):
            self.logger.info(f"Using cached robots.txt file for '{self.domain}'...")
            with open(robots_txt_filepath, 'r') as f:
                content = f.read()
                self.rp.parse(content.splitlines())
    
        else: # Get the robots.txt file from the server if we don't have it.
            async with aiohttp.ClientSession() as session:
                try:
                    self.logger.info(f"Getting robots.txt from '{robots_url}'...")
                    async with session.get(robots_url, timeout=10) as response:  # 10 seconds timeout
                        if response.status == 200:
                            self.logger.info("robots.txt response ok")
                            content = await response.text()
                            self.rp.parse(content.splitlines())
                        else:
                            self.logger.warning(f"Failed to fetch robots.txt: HTTP {response.status}")
                            return None
                except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                    e_tuple = (e.__qualname__, e)
                finally:
                    if e_tuple:
                        mes = f"{e_tuple[0]} while fetching robots.txt from '{robots_url}': {e_tuple[1]}"
                        self.logger.warning(mes)
                        return None
                    else:
                        self.logger.info(f"Got robots.txt for {self.domain}")
                        self.logger.debug(f"content:\n{content}",f=True)

            # Save the robots.txt file to disk.
            if not os.path.exists(robots_txt_filepath):
                with open(robots_txt_filepath, 'w') as f:
                    f.write(content)

        # Set the request rate and crawl delay from the robots.txt file.
        self.request_rate: float = self.rp.request_rate(self.user_agent) or 0
        self.logger.info(f"request_rate set to {self.request_rate}")
        self.crawl_delay: int = int(self.rp.crawl_delay(self.user_agent))
        self.logger.info(f"crawl_delay set to {self.crawl_delay}")
        return
