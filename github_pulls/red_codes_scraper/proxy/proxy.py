import csv
from dataclasses import dataclass, field
from enum import Enum
import os
from pathlib import Path
import random
import logging


import aiohttp
import requests
import requests.auth


from .utils import open_csv_file_as_set, save_set_to_csv_file, validate_path_then_return_it


logger = logging.getLogger(__name__)

this_files_directory = os.path.dirname(os.path.realpath(__file__))
proxies_csv_file_path = os.path.join(this_files_directory, "proxies.csv")
used_proxies_csv_file_path = os.path.join(this_files_directory, "used_proxies.csv")
print(proxies_csv_file_path)
print(used_proxies_csv_file_path)

# Load in the fresh and used proxies from the CSV files.
_proxies_file_path = validate_path_then_return_it(proxies_csv_file_path)
_used_proxies_file_path = validate_path_then_return_it(used_proxies_csv_file_path)
_proxies_set = open_csv_file_as_set(_proxies_file_path)
_used_proxies_set = open_csv_file_as_set(_used_proxies_file_path)


# Get rid of the proxies we've already used.
_proxies_set.difference_update(_used_proxies_set)
if len(_proxies_set) == 0:
    logger.warning(f"WARNING: All the proxies in '{_proxies_file_path}' were already used. Skipping...")
else:
    logger.info(f"Loaded {len(_proxies_set)} proxies from {_proxies_file_path}.")


# TODO Define custom headers to suite the library.
_REQUESTS_HEADERS = _AIOHTTP_HEADERS = _PLAYWRIGHT_HEADERS= {
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 \
        (KHTML, like Gecko) Chrome/84.0.4147.135 Safari/537.36",
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.5',
    'accept-encoding': 'gzip, deflate, br',
    'dnt': '1',
    'connection': 'keep-alive',
    'upgrade-insecure-requests': '1',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'cache-control': 'max-age=0',
}


class _LibraryType(Enum):
    """
    Enumeration of supported HTTP library types.

    Attributes:
        REQUESTS: Represents the 'requests' library.
        AIOHTTP: Represents the 'aiohttp' library for asynchronous HTTP requests.
        PLAYWRIGHT: Represents the 'playwright' library for browser automation.
    """
    REQUESTS = "requests"
    AIOHTTP = "aiohttp"
    PLAYWRIGHT = "playwright"


@dataclass
class Proxies:
    """
    Container for proxies to feed to an HTTP request.

    Attributes:
        library (_LibraryType): The type of library the proxy will be used with. Options are REQUESTS, AIOHTTP, and PLAYWRIGHT.
        credentials (str): Proxies credentials in the format 'username:password'.
        username (str): Proxies username (extracted from credentials if provided).
        password (str): Proxies password (extracted from credentials if provided).
        auto_add_proxy_to_proxy_auth (bool): If True, automatically adds the proxy to the proxy authentication.
    
    Properties:
        proxy_auth: Returns the appropriate authentication object based on the library type.
        proxy: Returns a dictionary of proxy URLs or a single proxy URL, depending on the library type.

    Note:
        The class automatically manages a set of used proxies and saves them to a CSV file upon object deletion.
    """

    library: _LibraryType = field(default_factory=_LibraryType.REQUESTS, metadata={
        'options': (_LibraryType.REQUESTS, _LibraryType.AIOHTTP, _LibraryType.PLAYWRIGHT)
    })
    credentials: str = None
    username: str = None
    password: str = None
    auto_add_proxy_to_proxy_auth: bool = field(default_factory=True)
    _num_proxies_returned: int = 3 # For the three sections in a dictionary of "http", "https", and "ftp"
    _proxy_auth: requests.auth.HTTPBasicAuth | aiohttp.BasicAuth | dict = field(init=False)
    _used_proxies: set = field(default_factory=set())


    def __post_init__(self):

        # Get the username and password from credentials
        if self.credentials:
            if ':' not in self.credentials:
                logger.warning("Credentials must be in 'username:password' format. Skipping...")
            else:
                self.username, self.password = self.credentials.split(':', 1)
        elif not (self.username and self.password):
            logger.info("Username and/or password not provided. Leaving both as None...")

        self._proxy_auth = self._create_auth()


    def _create_auth(self) -> requests.auth.HTTPBasicAuth | aiohttp.BasicAuth | dict[str, str]:
        """
        Creates and returns the appropriate authentication object based on the library type.

        Returns:
            requests.auth.HTTPBasicAuth: For requests library.
            aiohttp.BasicAuth: For aiohttp library.
            dict[str, str]: For playwright library, containing username, password, and optionally the proxy server.

        Raises:
            ValueError: If an unsupported library type is specified.

        Note:
            For playwright, if auto_add_proxy_to_proxy_auth is True, the proxy server will be included in the returned dictionary.
        """
        auth_map = {
            _LibraryType.REQUESTS: lambda: requests.auth.HTTPBasicAuth(self.username, self.password),
            _LibraryType.AIOHTTP: lambda: aiohttp.BasicAuth(login=self.username, password=self.password),
            _LibraryType.PLAYWRIGHT: lambda: {
                "username": self.username,
                "password": self.password,
                **({"server": self.proxy} if self.auto_add_proxy_to_proxy_auth else {})
            }
        }
        if self.library not in auth_map:
            raise ValueError(f"Unsupported library: {self.library}")

        return auth_map[self.library]()

    def __del__(self):
        # Save the used proxies to the used proxies CSV upon garbage collection.
        if self._used_proxies is not None:
            save_set_to_csv_file(self._used_proxies, _used_proxies_file_path)

    @property
    def proxy_auth(self) -> aiohttp.BasicAuth | requests.auth.HTTPBasicAuth | dict[str, str] | dict[None]:
        """
        Returns the proxy authentication object based on the selected library type.

        Returns:
            aiohttp.BasicAuth: For aiohttp library.
            requests.auth.HTTPBasicAuth: For requests library.
            dict[str, str]: For playwright library, containing username, password, and optionally the proxy server.
            dict[None]: An empty dictionary if no authentication is set.
        """
        return self._proxy_auth

    @property
    def proxy(self) -> dict[str, str] | str | None:
        """
        Retrieves and formats proxy information based on the library type.

        Returns:
            dict[str, str]: A dictionary containing proxy URLs for 'http', 'https', and 'ftp' 
                            when using Requests or Aiohttp libraries.
            str: A single proxy URL string when using the Playwright library.
            None: If no proxies are available or an error occurs.

        Behavior:
        - Attempts to randomly select a specified number of proxies from the available set.
        - Adds selected proxies to the used proxies set.
        - Returns formatted proxy information based on the library type.

        Notes:
        - For Requests and Aiohttp, returns a dictionary with keys 'http', 'https', and 'ftp'.
        - For Playwright, returns a single proxy URL as a string.
        - If there are not enough proxies available or an error occurs, returns None.
        """
        # Return proxies from the set as specified by _num_proxies_returned
        try:
            chosen_proxies: list[str] = random.sample(_proxies_set, k=self._num_proxies_returned)
        except ValueError:
            logger.warning("_proxies_set has run out of new proxies. Skipping...")
            return None

        if len(chosen_proxies) != self._num_proxies_returned:
            logger.warning("Mismatch between requested and available proxies. Skipping...")
            return None

        _ = [self._used_proxies.add(proxy) for proxy in chosen_proxies]

        if self.library in (_LibraryType.REQUESTS, _LibraryType.AIOHTTP):
            return {"http": chosen_proxies[0], "https": chosen_proxies[1], "ftp": chosen_proxies[2]}
        elif self.library == _LibraryType.PLAYWRIGHT:
            return chosen_proxies[0]
        else:
            logger.warning("Cannot parse proxy for an unknown library. Skipping...")
            return None

@dataclass
class Headers:
    """
    Container for headers to feed to an HTTP request.
    
    Attributes:
        library: The type of library the headers will be assigned to. Options are "requests", "aiohttp", and "playwright".
    """
    library: _LibraryType = field(default_factory=_LibraryType.REQUESTS, metadata={
        'options': (_LibraryType.REQUESTS, _LibraryType.AIOHTTP, _LibraryType.PLAYWRIGHT)
    })
    _requests_headers: dict = field(default_factory=_REQUESTS_HEADERS)
    _aiohttp_headers: dict = field(default_factory=_AIOHTTP_HEADERS)
    _playwright_headers: dict = field(default_factory=_PLAYWRIGHT_HEADERS)

    @property
    def headers(self) -> dict[str, str]:
        """
        Returns the appropriate headers based on the selected library type.
        Supported types are "requests", "aiohttp", and "playwright".

        Returns:
            dict[str, str]: A dictionary of headers specific to the library type.
        """
        match self.library:
            case _LibraryType.REQUESTS:
                return self._requests_headers
            case _LibraryType.AIOHTTP:
                return self._aiohttp_headers
            case _LibraryType.PLAYWRIGHT:
                return self._playwright_headers
            case _:
                return {}
