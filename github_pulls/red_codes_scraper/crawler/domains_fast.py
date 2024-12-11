import asyncio
import json
from typing import Any, Coroutine
from urllib.parse import urlparse, urlunparse


import aiofiles


class DomainsFast:

    def __init__(self,
                 domains_txt: str = "domains.txt",
                 domains_json: str = "domains.json"
                ):
        self.domains_txt: str = domains_txt
        self.domains_json: str = domains_json


    async def read_domains_from_file(self, file_path: str) -> list[str]:
        async with aiofiles.open(file_path, "r") as file:
            lines = await file.readlines()
            return [
                self.get_base_url(line.strip()) for line in lines if line.strip()
            ]


    # TODO: Do I need finish line?
    async def read_domains_from_input(self):
        domains = []
        print("Enter URLs (type 'Done' to finish):")
        while True:
            url = await asyncio.to_thread(input, "> ")
            url = url.strip()
            if url.lower() == "done":
                break
            if url:
                domains.append(self.get_base_url(url))
        return domains


    def get_base_url(self, url: str) -> str:
        """Extracts and normalizes the base URL from a full URL."""
        parsed_url = urlparse(url if urlparse(url).scheme else "https://" + url)
        if parsed_url.scheme == "http":
            parsed_url = parsed_url._replace(scheme="https")

        netloc = parsed_url.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]

        return urlunparse((parsed_url.scheme, netloc, "", "", "", ""))


    async def create_domains_json(domains: list[str]) -> None:
        data = {
            "domains": list(set(domains))
        }
        async with aiofiles.open("domains.json", "w") as json_file:
            await json_file.write(json.dumps(data, indent=2))


    async def main(self) -> None:
        if self.domains_txt:
            domains = await self.read_domains_from_file(self.domains_txt)
        else:
            domains = await self.read_domains_from_input()
        await self.create_domains_json(domains)


if __name__ == "__main__":
    domains_txt = "domains.txt"
    domains_json = "domains.json"
    domains_fast = DomainsFast(domains_txt=domains_txt, domains_json=domains_json)
    try:
        asyncio.run(domains_fast.main())
    except KeyboardInterrupt:
        print("domains_fast stopped.")
