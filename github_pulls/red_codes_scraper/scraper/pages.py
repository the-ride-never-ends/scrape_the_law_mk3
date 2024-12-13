import asyncio
import json
from urllib.parse import urlparse
from typing import Any, TypeVar

import logging

logger = logging.getLogger(__name__)

from bs4 import BeautifulSoup
# NOTE These are primarily for type-hinting.
from playwright.sync_api import (
    Playwright as SyncPlaywright_,
    sync_playwright, 
    Page as SyncPage, 
    Browser as SyncBrowser, 
    BrowserContext as SyncBrowserContext
)
from playwright.async_api import (
    async_playwright, 
    Playwright as AsyncPlaywright_,
    Page as AsyncPage, 
    Browser as AsyncBrowser, 
    BrowserContext as AsyncBrowserContext
)

from abc import ABC, abstractmethod

from ..proxy.proxy import Proxies


class BasePlaywright(ABC):

    def __init__(self, 
                 sitemaps_json: str = "sitemaps.json", 
                 wait_until: str = "networkidle"
                ) -> None:
        self.sitemaps_data: dict = {}
        self.wait_until: str = wait_until
        self.proxies: Proxies = Proxies()

        # Load sitemaps.json file to get the list of sitemap URLs
        with open(sitemaps_json, "r") as infile:
            self.sitemaps_data = dict(json.load(infile))

    def process_url(self, url: str) -> tuple[str, str]:
        """
        Extract page name and create a title from a given URL.

        This function parses the URL to extract the page name from the path
        and generates a title by capitalizing each word in the page name.
        Args:
            url (str): The full URL of the page.

        Returns:
            tuple[str, str]: A tuple containing two elements:
                - page_name (str): The extracted page name from the URL path.
                - title (str): A generated title based on the page name.

        Example:
            >>> process_url("https://example.com/blog/my-first-post")
            ('my-first-post', 'My First Post')
        """
        path = urlparse(url).path.strip("/")
        page_name = path.split("/")[-1] if path else "home"
        title = " ".join(word.capitalize() for word in page_name.split("-"))
        return page_name, title

    @abstractmethod
    def extract_urls_from_sitemap(self, page: SyncPage, sitemap_url: str) -> list[str]:
        pass

    @abstractmethod
    async def async_extract_urls_from_sitemap(self, page: AsyncPage, sitemap_url: str) -> list[str]:
        """
        Asynchronously parse a sitemap and extract URLs.

        This function navigates to the given sitemap URL using an asynchronous Playwright page,
        then parses the XML content to extract all URLs listed in the sitemap.

        Args:
            page (AsyncPage): An asynchronous Playwright page object.
            sitemap_url (str): The URL of the sitemap to parse.
            timeout (float, optional): Maximum navigation time in milliseconds. Defaults to 30000.0.
            wait_until (str, optional): When to consider navigation succeeded. Defaults to "networkidle".

        Returns:
            list[str]: A list of URLs extracted from the sitemap.

        Note:
            This function assumes the sitemap is in XML format and uses BeautifulSoup for parsing.
            It only extracts URLs from <loc> tags in the sitemap.
        """
        pass

    @abstractmethod
    def get_domain_pages() -> dict[list[dict[str, str]]]:
        pass

    @abstractmethod
    async def async_get_domain_pages() -> dict[list[dict[str, str]]]:
        pass

    @abstractmethod
    def data_validation(self) -> None:
        pass

    @abstractmethod
    def main() -> None:
        pass

    @abstractmethod
    async def async_main() -> None:
        pass


class AsyncPlaywright(BasePlaywright):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    async def async_extract_urls_from_sitemap(self,
                                              page: AsyncPage,
                                              sitemap_url: str,
                                              timeout: float = 30000.0,
                                              wait_until: str = "networkidle"
                                            ) -> list[str]:
        response = await page.goto(sitemap_url, timeout=timeout, wait_until=wait_until)
        urls = []

        if response and response.status == 200:
            soup = BeautifulSoup(response.text(), "lxml-xml")
            for loc in soup.find_all("loc"):
                url = loc.text.strip()
                urls.append(url)

        return urls

    async def async_get_domain_pages(self) -> dict[list[dict[str, str]]]:
        """
        Main function to generate pages.json
        """
        result = {}
        with async_playwright() as pw:
            pw: AsyncPlaywright_
            browser = await pw.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            for domain, sitemaps in self.sitemaps_data.items():
                domain_pages = []

                for sitemap in sitemaps:
                    sitemap_url = sitemap if isinstance(sitemap, str) else sitemap.get("url")  # Adjust here to get URL
                    if not sitemap_url:
                        continue

                    # Extract all page URLs from the current sitemap
                    urls = await self.async_extract_urls_from_sitemap(page, sitemap_url)

                    # Process each URL to get the page name and title
                    for url in urls:
                        page_name, title = self.process_url(url)
                        domain_pages.append({
                            "url": url,
                            "page_name": page_name,
                            "title": title
                        })

                result[domain] = domain_pages

            await browser.close()
        return result


    async def async_main(self):
        page_data = await self.async_get_domain_pages()
        # Save results to JSON
        with open("pages.json", "w") as outfile:
            json.dump(page_data, outfile, indent=2)
        logger.info("Pages have been saved to pages.json")



class SyncPlaywright(BasePlaywright):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def extract_urls_from_sitemap(self, 
                                  page: SyncPage, 
                                  sitemap_url: str,
                                  timeout: float = 30000.0,
                                  wait_until: str = "networkidle"
                                  ) -> list[str]:
        """
        Function to parse a sitemap and extract URLs
        """
        response = page.goto(sitemap_url, timeout=timeout, wait_until=wait_until)
        urls = []

        if response and response.status == 200:
            soup = BeautifulSoup(response.text(), "lxml-xml")
            for loc in soup.find_all("loc"):
                url = loc.text.strip()
                urls.append(url)

        return urls


    def get_domain_pages(self) -> dict[list[dict[str, str]]]:
        """
        Main function to generate pages.json
        """
        result = {}
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            for domain, sitemaps in self.sitemaps_data.items():
                domain_pages = []

                for sitemap in sitemaps:
                    sitemap_url = sitemap if isinstance(sitemap, str) else sitemap.get("url")  # Adjust here to get URL
                    if not sitemap_url:
                        continue

                    # Extract all page URLs from the current sitemap
                    urls = self.extract_urls_from_sitemap(page, sitemap_url)

                    # Process each URL to get the page name and title
                    for url in urls:
                        page_name, title = self.process_url(url)
                        domain_pages.append({
                            "url": url,
                            "page_name": page_name,
                            "title": title
                        })

                result[domain] = domain_pages

            browser.close()
        return result


    def main(self):
        page_data = self.get_domain_pages()
        # Save results to JSON
        with open("pages.json", "w") as outfile:
            json.dump(page_data, outfile, indent=2)
        logger.info("Pages have been saved to pages.json")


if __name__ == "__main__":
    try:
        use_async = input("Do you want to use asynchronous execution? (y/n): ").strip().lower() == "y"
        if use_async:
            async_get_pages = AsyncPlaywright()
            asyncio.run(async_get_pages.async_main())
        else:
            get_pages = SyncPlaywright()
            get_pages.main()
    except KeyboardInterrupt:
        print("pages stopped.")