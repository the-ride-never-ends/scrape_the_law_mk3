import aiohttp
import asyncio
from dataclasses import dataclass
import os
from typing import Any, Callable, Coroutine, Optional, OrderedDict, TypeVar, Union
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser


from bs4 import BeautifulSoup, PageElement, Tag, ResultSet
from playwright.async_api import (
    async_playwright, 
    Browser, 
    BrowserContext, 
    Page, 
    PlaywrightContextManager, 
    Playwright,
    Locator,
    FrameLocator,
)

Page.locator()
page = Page.get_by_role("button")



from utils.shared.make_id import make_id

from development.input_layer.autoscraper_web_scraper.auto_scraper_base_class import (
    BaseAutoScraper, 
    Stack,
    PlaywrightStack
)


T = TypeVar('T')


class Trigger():
    stack_list: list[Stack] = {}


class PlaywrightTrigger(Trigger):
    playwright_stack_list: list[Callable|Coroutine] = []


@dataclass
class PlaywrightStack(Stack):
    playwright_content: list[tuple[PlaywrightRule]] = None

    def __post_init__(self):
        super().__post_init__()

    @property
    def stack(self):
        return {
            'playwright_content': self.playwright_content,
            'content': self.content,
            'wanted_attr': self.wanted_attr,
            'is_full_url': self.is_full_url,
            'is_non_rec_text': self.is_non_rec_text,
            'url': self.url if self.is_full_url else "",
            'hash': self.hash,
            'stack_id': self.stack_id
        }


@dataclass
class Content:
    pass

from dataclasses import dataclass, field
from typing import Optional, Union, Callable, Any
from playwright.async_api import Page, Locator, ElementHandle


@dataclass
class PlaywrightRule:
    selector: Optional[str] = None
    coroutines_dict: Optional[OrderedDict['PlaywrightApiClass']] = None


    locator_info: dict[str, Any] = field(default_factory=lambda: {
        "frame_locator_str": None,
        "funcs": OrderedDict() ,
        "selector": None,
        "func_kwargs": None
    })
    action: Optional[str] = None
    action_args: dict[str, Any] = field(default_factory=dict)
    wait_for: Optional[str] = None
    timeout: int = 30000  # Default timeout in milliseconds

    async def execute(self, page: Page) -> Union[str, Locator, ElementHandle, None]:
        target = page
        
        # Handle frame locator if specified
        if self.locator_info["frame_locator_str"]:
            target = page.frame_locator(self.locator_info["frame_locator_str"])
        
        # Apply locator function if specified
        if self.locator_info["funcs"]:
            locator_func = getattr(target, self.locator_info["func"])
            target = locator_func(
                self.locator_info["selector"], 
                **self.locator_info.get("func_kwargs", {})
            )
        
        # Apply selector if specified
        elif self.selector:
            target = target.locator(self.selector)
        
        # Wait for element if specified
        if self.wait_for:
            await target.wait_for(state=self.wait_for, timeout=self.timeout)
        
        # Perform action if specified
        if self.action:
            action_method = getattr(target, self.action)
            return await action_method(**self.action_args)
        
        # Execute coroutine if specified
        if self.coroutines:
            return await self.coroutines(target)
        
        # Default: return the target
        return target

    @classmethod
    def create_click(cls, selector: str, **kwargs):
        return cls(selector=selector, action="click", **kwargs)

    @classmethod
    def create_fill(cls, selector: str, value: str, **kwargs):
        return cls(selector=selector, action="fill", action_args={"value": value}, **kwargs)

    @classmethod
    def create_type(cls, selector: str, text: str, **kwargs):
        return cls(selector=selector, action="type", action_args={"text": text}, **kwargs)

@dataclass
class PlaywrightClassAttributes:
    _methods: dict[str, Any] = None
    _properties: dict[str, Any] = None
    _events: dict[str, Any] = None


    def __post_init__(self):
        pass














    @property
    def methods(self):
        return {

        }

    @property
    def properties(self):
        return {

        }

    @property
    def events(self):
        return {

        }



@dataclass
class PlaywrightApiClassAssertions:
    api_responser_assertions: Any
    locator_assertions: Any
    page_assertions: Any


@dataclass
class PlaywrightStartUp:
    playwright_instance: Playwright = None


@dataclass
class PlaywrightApiClasses:
    api_request: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    api_request_context: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    api_response: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    accessibility: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    browser: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    browser_context: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    browser_type: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    cdp_session: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    console_message: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    clock: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    console_message: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    dialog: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    download: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    element_handle: ElementHandle = field(default_factory=list)
    error: Callable[..., Union[str, Locator, ElementHandle, None]] = field(default_factory=list)
    file_chooser: Callable
    frame: Callable
    frame_locator: Callable
    js_handle: Callable
    keyboard: Callable
    locator: Callable
    mouse: Callable
    page: Page
    request: Callable
    route: Callable
    selector: Callable
    timeout_error: Callable
    touchscreen: Callable
    tracing: Callable
    video: Callable
    web_error: Callable
    web_socket: Callable
    web_socket_route: Callable
    worker: Callable



@dataclass
class PlaywrightApiAssertions:
    pass


class PlaywrightAutoScraper(BaseAutoScraper):
    """
    AutoScraper implementation using Playwright for JavaScript-rendered content
    """
    
    def __init__(self, 
                 stack_list: list[PlaywrightStack|Stack] = None, 
                 browser_type: str = "chromium", 
                 post_processing: dict = None,
                 id: int = None,
                 **kwargs
                ):
        super().__init__(stack_list=stack_list, post_processing=post_processing)
        self.browser_type: Browser = browser_type
        self._playwright: Playwright = None
        self._browser: Browser = None
        self._kwargs: dict[str, Any] = kwargs


    async def enter(self) -> None:
        self._playwright = await async_playwright().start()
        browser_launch = getattr(self._playwright, self.browser_type)
        self._browser = await browser_launch.launch(self, **self._kwargs)


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


    async def _execute_playwright_stack(self):
        self.stack_list


    async def _fetch_html(self, url: str, request_args: Optional[dict[str, Any]] = None) -> str:
        if not self._browser:
            raise RuntimeError("Browser not initialized. Use 'async with' context manager.")
        

        if 

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



