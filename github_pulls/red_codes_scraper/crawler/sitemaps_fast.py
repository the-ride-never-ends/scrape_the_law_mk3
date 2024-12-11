import asyncio
import json
from typing import Any, Coroutine

import aiofiles
import aiohttp
from bs4 import BeautifulSoup
from tqdm import asyncio as tqdmasyncio


from ..proxy.proxy import Proxy, Headers


MAX_CONNECTIONS = 5


async def run_task_with_limit(task: Coroutine) -> Any:
    """
    Set up rate-limit-conscious functions
    """
    stop_condition = None
    semaphore = asyncio.Semaphore(MAX_CONNECTIONS)

    async with semaphore:
        result = await task
        if result == stop_condition:
            global stop_signal
            stop_signal = True
        return result 


class SiteMapsFast:

    def __init__(self,
                 domains_json: str = "domains.json",
                 progressbar: bool = True,
                 **kwargs
                ):
        self.domains_json: str = domains_json
        self.progressbar: bool = progressbar
        self.proxies: Proxy = Proxy(library="aiohttp", **kwargs)


    # TODO: Is it a good idea to have response 200. or it's better trace all statuses and if status was 200 then do it
    async def load_domains(self) -> dict:
        """
        Pass
        """
        async with aiofiles.open(self.domains_json, "r") as infile:
            content = await infile.read()
            return json.loads(content)


    async def fetch_robots(self, 
                           session: aiohttp.ClientSession, 
                           domain_url: str
                          ) -> list[str]:
        """
        Pass
        """
        robots_url = f"{domain_url}/robots.txt"
        async with session.get(robots_url) as response:
            if response.status == 200:
                text = await response.text()
                sitemaps = [
                    line.split(":", 1)[1].strip()
                    for line in text.splitlines()
                    if line.startswith("Sitemap:")
                ]
                sitemaps = sitemaps if sitemaps else [f"{domain_url}/sitemap.xml"]
            else:
                sitemaps = [f"{domain_url}/sitemap.xml"]
            await asyncio.sleep(0.250)
            return sitemaps


    async def extract_urls_from_sitemap(self, 
                                        session: aiohttp.ClientSession, 
                                        sitemap_url: str
                                        ) -> list[str] | list:
        """
        Pass
        """
        async with session.get(sitemap_url) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, "lxml-xml")
                urls = [loc.text.strip() for loc in soup.find_all("loc")]
            else:
                urls = []
        await asyncio.sleep(0.250)
        return urls


    async def process_domain(self, 
                             session: aiohttp.ClientSession, 
                             domain_url: str, 
                             sitemaps: dict
                            ) -> None:
        """
        Pass
        """
        sitemap_urls = await self.fetch_robots(session, domain_url)
        all_urls = []
        for sitemap_url in sitemap_urls:
            urls = await self.extract_urls_from_sitemap(session, sitemap_url)
            all_urls.extend(urls)
        sitemaps[domain_url] = all_urls


    async def get_sitemaps_from_domains(self, 
                                        domains: list[str]
                                        ) -> dict:
        """
        Pass
        """
        sitemaps = {}
        async with aiohttp.ClientSession() as session:
            tasks = [
                self.process_domain(session, domain_url, sitemaps) for domain_url in domains
            ]
            tasks_with_limit = [
                run_task_with_limit(task) for task in tasks
            ]
            if self.progressbar:
                for future in tqdmasyncio.tqdm.as_completed(tasks_with_limit):
                    if future is None:
                        break
                    await future
            else:
                await asyncio.gather(*tasks_with_limit)
        return sitemaps


    async def create_sitemaps_json(sitemaps: dict) -> None:
        """
        Pass
        """
        async with aiofiles.open("sitemaps.json", "w") as outfile:
            await outfile.write(json.dumps(sitemaps, indent=2))


    async def main(self) -> None:
        """
        Pass
        """
        domains_data = await self.load_domains()
        sitemaps = await self.get_sitemaps_from_domains(domains_data["domains"])
        await self.create_sitemaps_json(sitemaps)


if __name__ == "__main__":
    site_maps_fast = SiteMapsFast()
    try:
        asyncio.run(site_maps_fast.main())
    except KeyboardInterrupt:
        print("sitemaps_fast stopped.")
