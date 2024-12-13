from abc import ABC, abstractmethod
import asyncio
from collections import defaultdict, OrderedDict
import hashlib
from html import unescape
import inspect
import json
import logging
import os
import pathlib
import pickle
from typing import (
    Any, 
    Callable, 
    Generator,
    Iterable, 
    Optional, 
    OrderedDict as OrderedDict_ , 
    Pattern, 
    Type,
    TypeVar, 
    Never
)
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET


import aiohttp
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup, PageElement, Tag, ResultSet
import duckdb
import yaml

from utils.shared.make_id import make_id
from utils.shared.sanitize_filename import sanitize_filename
from .file_path_to_dict import file_path_to_dict
from database.mysql_database import MySqlDatabase
from logger.logger import Logger

from dataclasses import dataclass

from .utils import (
    FuzzyText,
    ResultItem,
    get_non_rec_text,
    get_random_str,
    normalize,
    text_match,
    unique_hashable,
    unique_stack_list,
)

def dict_to_string_iterable(input_dict: dict) -> Iterable[str]:
    """
    Convert a dictionary to robots.txt format strings.
    Handles nested dictionaries and lists.
    """
    for key, value in input_dict.items():
        if isinstance(value, dict):
            # Handle nested user agent sections
            yield f"User-agent: {key}"
            for sub_key, sub_value in value.items():
                if isinstance(sub_value, list):
                    for item in sub_value:
                        yield f"{sub_key}: {item}"
                else:
                    yield f"{sub_key}: {sub_value}"
        elif isinstance(value, list):
            # Handle lists of values (e.g., multiple Disallow entries)
            for item in value:
                yield f"{key}: {item}"
        else:
            # Handle simple key-value pairs
            yield f"{key}: {value}"


def type_check_stack_list(stack_list: Any) -> Never:

    # Check if stack_list is a valid list
    if stack_list is not None:
        if not isinstance(stack_list, list):
            raise TypeError("stack_list must be a list")
            
        # Check each item in the stack_list
        for item in stack_list:
            if not isinstance(item, dict):
                raise ValueError("Each item in stack_list must be a dictionary")

            # Check for required fields in each stack item
            required_fields = ['content', 'wanted_attr', 'is_full_url', 'url', "is_non_rec_text"]
            for field in required_fields:
                if field not in item:
                    raise ValueError(f"Missing required field '{field}' in stack item")

this_files_directory = os.path.dirname(os.path.realpath(__file__))

from dataclasses import dataclass, field
import hashlib
from typing import Optional
from .utils import get_random_str

from dataclasses import dataclass, field
import hashlib
from typing import Optional
from .utils import get_random_str

@dataclass
class Stack:
    """
    Attributes:
        - content: List of tuples describing HTML path
        - wanted_attr: Attribute to extract (if any)
        - is_full_url: Whether to resolve relative URLs
        - is_non_rec_text: Whether to use non-recursive text
        - url: Base URL for resolving links
        - hash: Unique hash (automatically updated)
        - stack_id: Random identifier (generated at Stack instantiation, immutable)
    """
    content: list[tuple[str, dict, Optional[int]]]
    wanted_attr: Optional[str]
    is_full_url: bool
    is_non_rec_text: bool
    url: str
    hash: str = field(init=False, compare=False)
    stack_id: str = field(default_factory=lambda: "rule_" + get_random_str(4), init=False)

    def __post_init__(self):
        self._update_hash()

    def _update_hash(self):
        """Update the hash based on current attribute values."""
        self.hash = hashlib.sha256(str(self.__dict__).encode("utf-8")).hexdigest()

    def __setattr__(self, name, value):
        """Override setattr to update hash when any attribute changes."""
        super().__setattr__(name, value)
        if name != 'hash':  # Prevent recursive calls when updating hash
            self._update_hash()

    @property
    def stack(self):
        return {
            'content': self.content,
            'wanted_attr': self.wanted_attr,
            'is_full_url': self.is_full_url,
            'is_non_rec_text': self.is_non_rec_text,
            'url': self.url if self.is_full_url else "",
            'hash': self.hash,
            'stack_id': self.stack_id
        }



from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID
from typing import Optional, Any

class DocumentStatus(Enum):
    """
    Enumeration representing the possible statuses of a document.

    Attributes:
        NEW (str): Indicates that the document is newly added and hasn't been processed yet.
        PROCESSING (str): Indicates that the document is currently being processed.
        COMPLETE (str): Indicates that the document has been successfully processed.
        ERROR (str): Indicates that an error occurred during document processing.
    """
    NEW = "new"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"

class JobStatus(Enum):
    """
    Enumeration representing the possible statuses of a processing job.

    Attributes:
        PENDING (str): Indicates that the job is waiting to be processed.
        RUNNING (str): Indicates that the job is currently being processed.
        COMPLETE (str): Indicates that the job has finished processing successfully.
        FAILED (str): Indicates that the job encountered an error during processing.
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"

@dataclass
class Document:
    document_id: UUID
    source_id: UUID
    url: str
    scraping_config: dict[str, Any] = {
        "stack": Stack,
        "robots": str,
    }
    last_scrape: Optional[datetime]
    last_successful_scrape: Optional[datetime]
    current_version_id: Optional[UUID]
    status: DocumentStatus
    priority: int
    document_type: str

    def __post_init__(self):
        if len(self.url) > 2200:
            raise ValueError("URL must not exceed 2200 characters")
        if not 1 <= self.priority <= 5:
            raise ValueError("Priority must be between 1 and 5")

class PlaywrightStack:
    pass

# TODO 
@dataclass
class ProcessingJob:
    job_id: UUID
    document_id: UUID
    status: JobStatus
    processor_type: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_config: dict[str, Any]

@dataclass
class Trigger:
    document_id: UUID


@dataclass
class TriggerList:
    _trigger_list: list[Trigger]
    yield_size: int

    def __post_init__(self):
        if self.yield_size <= 0:
            raise ValueError("yield_size must be a positive integer")

    @property
    def trigger_list(self) -> Generator:
        for i in range(0, len(self._trigger_list), self.yield_size):
            yield self._trigger_list[i:i + self.yield_size]



from .proxies.proxies import Proxies, Headers
from utils.shared.open_and_save_any_file.file_openers.file_opener import FileOpener


class UniversalFileSaver:

    def __init__(self):
        pass


T = TypeVar('T')
open_ = FileOpener()
save_ = UniversalFileSaver()


class PlaywrightStack(T):
    pass


class BaseAutoScraper(ABC):
    """
    AutoScraper : A Smart, Automatic, Fast and Lightweight Web Scraper for Python.
    AutoScraper automatically learns a set of rules required to extract the needed content
        from a web page. So the programmer doesn't need to explicitly construct the rules.

    Parameters
    ----------
    stack_list: list
        List of rules learned by AutoScraper
    post_processing_functions_dict: OrderedDict[str, Callable]
        Dictionary of functions and their names to be used to process raw HTML after escaping and normalization.
    pre_processing_functions_dict: OrderedDict[str, Callable]
        Dictionary of functions and their names to be used to process raw HTML before escaping and normalization.
    robots_txt_filepath: str
        Path to a robots.txt file. Filepath can be a canonical path or an ID for a robots.txt file in a database.
    trigger: Trigger dataclass
        pass
    headers: Headers dataclass
        pass
    proxies: Proxies dataclass
        pass
    id_: int
        Unique UUID for this scraper instance.

    Attributes
    ----------
    stack_list: list
        List of rules learned by AutoScraper

    Methods
    -------
    build() - Learns a set of rules represented as stack_list based on the wanted_list,
        which can be reused for scraping similar elements from other web pages in the future.
    get_result_similar() - Gets similar results based on the previously learned rules.
    get_result_exact() - Gets exact results based on the previously learned rules.
    get_results() - Gets exact and similar results based on the previously learned rules.
    save() - Serializes the stack_list as JSON and saves it to disk.
    load() - De-serializes the JSON representation of the stack_list and loads it back.
    remove_rules() - Removes one or more learned rule[s] from the stack_list.
    keep_rules() - Keeps only the specified learned rules in the stack_list and removes the others.
    """

    def __init__(self, 
                 stack_list: list[PlaywrightStack|Stack] = None, 
                 post_processing_functions_dict: Optional[OrderedDict_[str, Callable]] = None,
                 pre_processing_functions_dict: Optional[OrderedDict_[str, Callable]] = None,
                 robots_txt_filepath: Optional[str] = None,
                 trigger: Optional[Trigger] = None,
                 headers: Optional[Headers] = None,
                 proxies: Optional[Proxies] = None,
                 id_: int = make_id()
                ) -> None:
        """
        Initialize the scraper with optional stack list and post-processing functions.
        
        Args:
            stack_list: List of scraping rules
            post_processing_functions_dict: Ordered Dictionary of functions to process HTML before parsing
        """
        self.id = id_
        if stack_list is not None:
            type_check_stack_list(stack_list)
        self.stack_list: list = stack_list or []

        if post_processing_functions_dict is not None:
            self.type_check_processing_functions_dict(post_processing_functions_dict)
        if pre_processing_functions_dict is not None:
            self.type_check_processing_functions_dict(pre_processing_functions_dict)

        self.post_processing_functions_dict: OrderedDict_[str, Callable] = post_processing_functions_dict or OrderedDict()
        self.pre_processing_functions_dict: OrderedDict_[str, Callable] = pre_processing_functions_dict or OrderedDict()

        
        self.logger: Logger = Logger(logger_name=f"{self.__class__.__module__}__{self.__class__.__name__}__{str(self.id)}")
        self.trigger: Trigger = trigger
        self.request: Headers = headers
        self.proxies: Proxies - proxies

        self.domain = "www.example.com" if trigger is None else self.trigger.url
        self.robots_txt_filepath: str = robots_txt_filepath or os.path.join(this_files_directory, urljoin(self.domain, 'robots.txt'))
        self.user_agent = "*" if headers is None else self.request.headers['user_agent']
        self.rp: RobotFileParser = None
        self.request_rate: float = None
        self.crawl_delay: int = None

    @staticmethod
    def type_check_processing_functions_dict(post_processing_functions_dict: OrderedDict_) -> Never:

        for func in post_processing_functions_dict.values():
            if not isinstance(func, Callable):  # Make sure it's a function (as opposed to a coroutine.)
                raise TypeError(f"function {func} is not a Callable, but a {type(func)}")

            # Check if the function has 1 positional argument and that that argument is a string.
            sig = inspect.signature(func)
            params = list(sig.parameters.values())

            if len(params) != 1: # Check if it has one positional argument (i.e. for HTML)
                raise ValueError(f"Function {func.__name__} must have exactly one positional argument")

            if params[0].annotation != str: # Check if the positional argument is typed as a string.
                raise TypeError(f"Argument for Function {func.__name__} must be str. Instead, it was a {type(params[0].annotation)}")


    def save(self, file_path: str, data: dict = None):
        """
        Serializes the stack_list as JSON and saves it to the disk.

        Args:
            file_path: Path of the JSON output.

        Returns:
            None.
        """
        data = data or dict(stack_list=self.stack_list)
        with open(file_path, "w") as f:
            json.dump(data, f)


    def load(self, file_path: str) -> None: # -> str | list[str]
        """
        De-serializes the JSON representation of the stack_list and loads it back.

        Args:
            file_path (str): Path of the JSON file to load stack_list from.
        """
        # Get the data from the file.
        # NOTE: Supported types include "json", "log", "yaml/yml", "csv", "xml", 
        # "sqlite", "mysql", "pickle/pkl", "db", and "txt" files.
        data: dict = open_.this_file(file_path, and_return_a_=dict)
        if data is None:
            raise TypeError("data dictionary is None. Check to make sure the file was loaded correctly.")

        if "robots" in file_path or any(key in data for key in ["User-agent", "Allow", "Disallow", "Sitemap"]):
            # Check if we already got the robots.txt file for this website
            # If we do, load it in.
            robot_rules = list(dict_to_string_iterable(data))
            self.logger.debug(f"Parsed robots.txt rules:\n{'\n'.join(robot_rules)}")
            self.rp.parse(robot_rules)
        else: 
            if "stack_list" not in data:
                raise KeyError(f"Expected 'stack_list' key in data but found keys: {list(data.keys())}")

            stack_list = data["stack_list"]
            # Convert lists back to tuples in content field
            for stack in stack_list:
                if "content" in stack:
                    stack["content"] = [
                        tuple(item) if isinstance(item, list) else item 
                        for item in stack["content"]
                    ]
            self.stack_list = stack_list


    def validate_url(self, url: Optional[str]) -> None:
        if url is not None and not url.startswith(('http://', 'https://')):
            raise ValueError("URL must start with http:// or https://")


    async def __aenter__(self):
        return await self


    async def __aexit__(self, exc_type, exc_value, traceback):
        return await self.async_exit()


    @classmethod
    async def async_enter(cls, *args, **kwargs):
        instance = cls(*args, **kwargs)
        await instance.async_get_robots_rules()
        return instance


    async def __aenter__(self):
        await self.async_get_robots_rules()
        return self


    async def async_exit(cls):
        return


    @abstractmethod
    def _fetch_html(self, url, request_args=None) -> str:
        """
        - Purpose: Fetches HTML content from a URL
        - Process:
        1. Merges default and user-provided headers
        2. Extracts host from URL and adds to headers
        3. Makes GET request with custom headers
        4. Handles encoding intelligently:
            - Checks if ISO-8859-1 is correct encoding
            - Uses apparent_encoding if needed
        - Returns: HTML text content
        """
        pass


    @abstractmethod
    async def _async_fetch_html(self, url: str, request_args: Optional[dict[str, Any]] = None) -> str:
        """
        - Purpose: Asynchronously fetches HTML content from a URL
        - Process:
        1. Merges default and user-provided headers
        2. Extracts host from URL and adds to headers
        3. Makes GET request with custom headers
        4. Handles encoding intelligently:
            - Checks if ISO-8859-1 is correct encoding
            - Uses apparent_encoding if needed
        - Returns: HTML text content
        """
        pass


    async def _async_get_robots_rules(self, robots_url: str) -> str | None:
        async with aiohttp.ClientSession() as session:
            try:
                self.logger.info(f"Getting robots.txt from '{robots_url}'...")
                async with session.get(robots_url, timeout=10) as response:  # 10 seconds timeout
                    if response.status == 200:
                        self.logger.info("robots.txt response ok")
                        content = await response.text()
                        self.rp.parse(content.splitlines())
                        self.logger.info(f"Got robots.txt for {self.domain}")
                        self.logger.debug(f"content:\n{content}",f=True)
                        return content
                    else:
                        self.logger.warning(f"Failed to fetch robots.txt: HTTP {response.status}")
                        return None
            except (asyncio.TimeoutError, aiohttp.ClientError) as e:
                mes = f"{e.__str__()} while fetching robots.txt from '{robots_url}': {e}"
                self.logger.warning(mes)
                return None


    # Define class enter and exit methods.
    async def async_get_robots_rules(self) -> None:
        """
        Get the site's robots.txt file and read it asynchronously with a timeout.
        TODO Make a database of robots.txt files. This might be a good idea for scraping.
        """
        we_dont_got_it, robots_url = self.load_robot_rules_if_we_already_have_them()

        if we_dont_got_it:
            # Get the robots.txt file from the server if we don't have it.
            content = await self._async_get_robots_rules(robots_url)
            
            # Save the robots.txt file to disk.
            self.logger.debug("")
            if not os.path.exists(self.robots_txt_filepath):
                self.save(self.robots_txt_filepath, data=content)

        self.set_robot_rules()
        return


    def load_robot_rules_if_we_already_have_them(self):
        robots_url = urljoin(self.domain, 'robots.txt')
        self.rp = RobotFileParser(robots_url)
        if os.path.exists(self.robots_txt_filepath):
            self.logger.info(f"Using cached robots.txt file for '{self.domain}'...")
            self.load(self.robots_txt_filepath)
            return False, robots_url
        else: 
            return True, robots_url


    def set_robot_rules(self) -> None:
        # Set the request rate and crawl delay from the robots.txt file.
        self.request_rate: float = self.rp.request_rate(self.user_agent) or 0.0
        self.logger.info(f"request_rate set to {self.request_rate}")
        self.crawl_delay: int = int(self.crawl_delay) if self.crawl_delay is not None else 0
        self.logger.info(f"crawl_delay set to {self.crawl_delay}")
        return


    def get_robot_rules(self) -> list:
        we_dont_got_it, robots_url = self.load_robot_rules_if_we_already_have_them()
        if we_dont_got_it:
            # Get the robots.txt file from the server if we don't have it.
            content = self._get_robots_rules(robots_url)
            
            # Save the robots.txt file to disk.
            if not os.path.exists(self.robots_txt_filepath):
                self.save(self.robots_txt_filepath, data=content)

        self.set_robot_rules()
        return


    def _get_robots_rules(self, robots_url: str) -> list:
        try:
            self.logger.info(f"Getting robots.txt from '{robots_url}'...")
            response = requests.get(robots_url, timeout=10)  # 10 seconds timeout
            if response.status_code == 200:
                self.logger.info("robots.txt response ok")
                content = response.text
                self.rp.parse(content.splitlines())
                self.logger.info(f"Got robots.txt for {self.domain}")
                self.logger.debug(f"content:\n{content}", f=True)
                return content
            else:
                self.logger.warning(f"Failed to fetch robots.txt: HTTP {response.status_code}")
                return None
        except RequestException as e:
            mes = f"{e.__class__.__name__} while fetching robots.txt from '{robots_url}': {e}"
            self.logger.warning(mes)
            return None


    async def _async_get_soup(self, 
                              url: Optional[str] = None, 
                              html: Optional[str] = None, 
                              request_args: Optional[dict[str, Any]] = None
                            ) -> BeautifulSoup:
        """Creates BeautifulSoup parser object from HTML or URL.

        This method can work with either direct HTML content or a URL. If HTML is
        provided, it normalizes and parses it. If a URL is provided, it fetches the
        content first, then parses it.

        Args:
            url: Optional URL to fetch HTML from.
            html: Optional HTML string to parse directly.
            request_args: Optional dictionary of arguments for the HTTP request.

        Returns:
            A BeautifulSoup object using the 'lxml' parser.

        Raises:
            ValueError: If neither url nor html is provided.
        """
        if html:
            return self._process_soup(html=html)

        html = await self._async_fetch_html(url, request_args)
        return self._process_soup(html=html)


    def _get_soup(self, 
                  url: Optional[str] = None, 
                  html: Optional[str] = None, 
                  request_args: Optional[dict[str, Any]] = None
                ) -> BeautifulSoup:
        """Asynchronously creates BeautifulSoup parser object from HTML or URL.

        This method can work with either direct HTML content or a URL. If HTML is
        provided, it normalizes and parses it. If a URL is provided, it fetches the
        content first, then parses it.

        Args:
            url: Optional URL to fetch HTML from.
            html: Optional HTML string to parse directly.
            request_args: Optional dictionary of arguments for the HTTP request.

        Returns:
            A BeautifulSoup object using the 'lxml' parser.

        Raises:
            ValueError: If neither url nor html is provided.
        """
        if html:
            return self._process_soup(html)

        html = self._fetch_html(url, request_args)
        return self._process_soup(html)


    def _post_process_soup(self, html: str) -> str:
        self.logger.debug(f"Post processing functions passed\n{self.post_processing_functions_dict}")

        for func in self.post_processing_functions_dict.values():
            html = func(html)

        return html


    def _process_soup(self, html: str):
        html = normalize(unescape(html))
        if self.post_processing_functions_dict:
            html = self._post_process_soup(html)
        return BeautifulSoup(html, "lxml")


    @staticmethod
    def _get_valid_attrs(item) -> dict[str, str]:
        """
        - Purpose: Extracts relevant attributes from HTML elements
        - Process:
            1. Focuses on 'class' and 'style' attributes
            2. Converts empty lists to empty strings
            3. Ensures both attributes exist in result
        - Returns: Dictionary of cleaned attributes
        """
        key_attrs = {"class", "style"}
        attrs = {
            k: v if v != [] else "" for k, v in item.attrs.items() if k in key_attrs
        }

        for attr in key_attrs:
            if attr not in attrs:
                attrs[attr] = ""
        return attrs


    @staticmethod
    def _child_has_text(child: PageElement, 
                        text: str, 
                        url: str, 
                        text_fuzz_ratio: float
                        ) -> bool:
        """
        - Purpose: Checks if element contains target text
        - Checks multiple locations:
            1. Direct text content
            2. Non-recursive text content
            3. Attribute values
            4. URL attributes (href/src) with base URL resolution
        - Features:
            - Fuzzy matching support
            - Handles full URL resolution
            - Marks match location for later use
        - Returns: Boolean indicating match found
        """

        child_text = child.getText().strip()

        if text_match(text, child_text, text_fuzz_ratio):
            parent_text = child.parent.getText().strip()
            if child_text == parent_text and child.parent.parent:
                return False

            child.wanted_attr = None
            return True

        if text_match(text, get_non_rec_text(child), text_fuzz_ratio):
            child.is_non_rec_text = True
            child.wanted_attr = None
            return True

        for key, value in child.attrs.items():
            if not isinstance(value, str):
                continue

            value = value.strip()
            if text_match(text, value, text_fuzz_ratio):
                child.wanted_attr = key
                return True

            if key in {"href", "src"}:
                full_url = urljoin(url, value)
                if text_match(text, full_url, text_fuzz_ratio):
                    child.wanted_attr = key
                    child.is_full_url = True
                    return True

        return False

    def _get_children(self, 
                      soup: BeautifulSoup, 
                      text: str, 
                      url: str, 
                      text_fuzz_ratio: float
                    ) -> list[Any]:
        """
        - Purpose: Finds all elements containing target text
        - Process:
            1. Gets all descendants in reverse order
            2. Filters using _child_has_text
        - Returns: List of matching elements
        """
        children = reversed(soup.findChildren())
        children = [
            x for x in children if self._child_has_text(x, text, url, text_fuzz_ratio)
        ]
        return children
    

    async def async_build(
        self,
        url: Optional[str] = None,
        wanted_list: list[str|Pattern] = None,
        wanted_dict: dict = None,
        html: Optional[str] = None,
        request_args: Optional[dict[str, Any]] = None,
        update: bool = False,
        text_fuzz_ratio: float = 1.0,
    ) -> list:
        soup = await self._async_get_soup(url=url, html=html, request_args=request_args)
        return self._build(soup, url, wanted_list, wanted_dict, text_fuzz_ratio, update)


    def build(
        self,
        url: Optional[str] = None,
        wanted_list: list[str|Pattern] = None,
        wanted_dict: dict = None,
        html: Optional[str] = None,
        request_args: Optional[dict[str, Any]] = None,
        update: bool = False,
        text_fuzz_ratio: float = 1.0,
    ) -> list:
        soup = self._get_soup(url=url, html=html, request_args=request_args)
        return self._build(soup, url, wanted_list, wanted_dict, text_fuzz_ratio, update)


    def _build(
        self,
        soup: str,
        url: Optional[str] = None,
        wanted_list: list[str|Pattern] = None,
        wanted_dict: dict = None,
        update: bool = False,
        text_fuzz_ratio: float = 1.0,
    ) -> list:
        """
        Automatically constructs a set of rules to scrape the specified target[s] from a web page.
            The rules are represented as stack_list.

        Parameters:
        ----------
        url: str, optional
            URL of the target web page. You should either pass url or html or both.

        wanted_list: list of strings or compiled regular expressions, optional
            A list of needed contents to be scraped.
                AutoScraper learns a set of rules to scrape these targets. If specified,
                wanted_dict will be ignored.

        wanted_dict: dict, optional
            A dict of needed contents to be scraped. Keys are aliases and values are list of target texts
                or compiled regular expressions.
                AutoScraper learns a set of rules to scrape these targets and sets its aliases.

        html: str, optional
            An HTML string can also be passed instead of URL.
                You should either pass url or html or both.

        request_args: dict[str, Any], optional
            A dictionary used to specify a set of additional request parameters used by requests
                module. You can specify proxy URLs, custom headers etc.

        update: bool, optional, defaults to False
            If True, new learned rules will be added to the previous ones.
            If False, all previously learned rules will be removed.

        text_fuzz_ratio: float in range [0, 1], optional, defaults to 1.0
            The fuzziness ratio threshold for matching the wanted contents.

        Returns:
        --------
        List of similar results
        """

        result_list = []

        if update is False:
            self.stack_list = []

        if wanted_list:
            wanted_dict = {"": wanted_list}

        wanted_list = []

        for alias, wanted_items in wanted_dict.items():
            wanted_items = [normalize(w) for w in wanted_items]
            wanted_list += wanted_items

            for wanted in wanted_items:
                children = self._get_children(soup, wanted, url, text_fuzz_ratio)

                for child in children:
                    result, stack = self._get_result_for_child(child, soup, url)
                    stack["alias"] = alias
                    result_list += result
                    self.stack_list.append(stack)

        result_list = [item.text for item in result_list]
        result_list = unique_hashable(result_list)

        self.stack_list = unique_stack_list(self.stack_list)
        return result_list


    @classmethod
    def _build_stack(cls, child: Tag, url: str) -> dict[str, str]:
        # 1. Start with content list - captures the HTML hierarchy
        content: list[tuple] = [(child.name, cls._get_valid_attrs(child))]

        # 2. Build up the path from child to root
        parent = child
        while True:
            grand_parent = parent.findParent()
            if not grand_parent:
                break

            children = grand_parent.findAll(
                parent.name, cls._get_valid_attrs(parent), recursive=False
            )
            for i, c in enumerate(children):
                if c == parent:
                    content.insert(
                        0, (grand_parent.name, cls._get_valid_attrs(grand_parent), i)
                    )
                    break

            if not grand_parent.parent:
                break

            parent = grand_parent

        # 3. Add metadata
        wanted_attr = getattr(child, "wanted_attr", None)
        is_full_url = getattr(child, "is_full_url", False)
        is_non_rec_text = getattr(child, "is_non_rec_text", False)
        stack = Stack(
            content=content,
            wanted_attr=wanted_attr,
            is_full_url=is_full_url,
            url=url,

        )
        stack = {
            "content": content, # List of tuples describing HTML path
            "wanted_attr": wanted_attr, # Attribute to extract (if any)
            "is_full_url": is_full_url, # bool: Whether to resolve relative URLs
            "is_non_rec_text": is_non_rec_text, # bool: Whether to use non-recursive text
            "url": url if is_full_url else "", # Base URL for resolving links
            "hash": hashlib.sha256(str(stack).encode("utf-8")).hexdigest(), # Unique hash of the stack itself
            "stack_id": "rule_" + get_random_str(4) # Arbitrary ID for the stack. Format: 'rule_3a3b'
        }
        return stack

    def _get_result_for_child(self, child, soup: BeautifulSoup, url: str):
        stack = self._build_stack(child, url)
        result = self._get_result_with_stack(stack, soup, url, 1.0)
        return result, stack

    @staticmethod
    def _fetch_result_from_child(child: PageElement, wanted_attr: Tag, is_full_url: bool, url: str, is_non_rec_text: bool):
        """
        - Purpose: Extracts desired content from matched element
        - Cases handled:
            1. Text content (recursive or non-recursive)
            2. Specific attribute value
            3. URL attributes with base resolution
        - Returns: Extracted content or None
        """
        if wanted_attr is None:
            if is_non_rec_text:
                return get_non_rec_text(child)
            return child.getText().strip()

        if wanted_attr not in child.attrs:
            return None

        if is_full_url:
            return urljoin(url, child.attrs[wanted_attr])

        return child.attrs[wanted_attr]


    @staticmethod
    def _get_fuzzy_attrs(attrs: dict, attr_fuzz_ratio: float):
        """
        - Purpose: Creates fuzzy-matchable attributes
        - Process:
        1. Converts string values to FuzzyText objects
        2. Handles both single values and lists
        3. Preserves non-string attributes
        - Returns: Dictionary with fuzzy-matchable values
        """
        attrs = dict(attrs)
        for key, val in attrs.items():
            if isinstance(val, str) and val:
                val = FuzzyText(val, attr_fuzz_ratio)
            elif isinstance(val, (list, tuple)):
                val = [FuzzyText(x, attr_fuzz_ratio) if x else x for x in val]
            attrs[key] = val
        return attrs

    def _get_result_with_stack(self, 
                               stack: list, 
                               soup: BeautifulSoup, 
                               url: str, 
                               attr_fuzz_ratio: float, 
                               **kwargs
                               ):
        """
        - Purpose: Finds matches using learned rule
        - Process:
            1. Traverses DOM following rule pattern
            2. Handles siblings and leaf nodes
            3. Extracts content from matches
        - Advanced features:
        - Keep_blank option
        - Sibling handling
        - Order preservation
        """
        parents = [soup]
        stack_content = stack["content"]
        contain_sibling_leaves = kwargs.get("contain_sibling_leaves", False)
        for index, item in enumerate(stack_content):
            children = []
            if item[0] == "[document]":
                continue
            for parent in parents:

                attrs = item[1]
                if attr_fuzz_ratio < 1.0:
                    attrs = self._get_fuzzy_attrs(attrs, attr_fuzz_ratio)

                found = parent.findAll(item[0], attrs, recursive=False)
                if not found:
                    continue

                if not contain_sibling_leaves and index == len(stack_content) - 1:
                    idx = min(len(found) - 1, stack_content[index - 1][2])
                    found = [found[idx]]

                children += found

            parents = children

        wanted_attr = stack["wanted_attr"]
        is_full_url = stack["is_full_url"]
        is_non_rec_text = stack.get("is_non_rec_text", False)
        result = [
            ResultItem(
                self._fetch_result_from_child(
                    i, wanted_attr, is_full_url, url, is_non_rec_text
                ),
                getattr(i, "child_index", 0),
            )
            for i in parents
        ]
        if not kwargs.get("keep_blank", False):
            result = [x for x in result if x.text]
        return result

    def _get_result_with_stack_index_based(
        self, stack: dict, soup: BeautifulSoup, url: str, attr_fuzz_ratio: float, **kwargs
    ):
        """
        - Purpose: Finds exact matches using position information
        - More strict than _get_result_with_stack
        - Returns: List of exact matches
        """
        p = soup.findChildren(recursive=False)[0]
        stack_content = stack["content"]
        for index, item in enumerate(stack_content[:-1]):
            if item[0] == "[document]":
                continue
            content = stack_content[index + 1]
            attrs = content[1]
            if attr_fuzz_ratio < 1.0:
                attrs = self._get_fuzzy_attrs(attrs, attr_fuzz_ratio)
            p = p.findAll(content[0], attrs, recursive=False)
            if not p:
                return []
            idx = min(len(p) - 1, item[2])
            p = p[idx]

        result = [
            ResultItem(
                self._fetch_result_from_child(
                    p,
                    stack["wanted_attr"],
                    stack["is_full_url"],
                    url,
                    stack["is_non_rec_text"],
                ),
                getattr(p, "child_index", 0),
            )
        ]
        if not kwargs.get("keep_blank", False):
            result = [x for x in result if x.text]
        return result

    async def _async_get_result_by_func(self,
        func: Callable,
        url: str,
        html: str,
        soup: BeautifulSoup,
        request_args: dict[str, Any],
        grouped: bool,
        group_by_alias: bool,
        unique: bool,
        attr_fuzz_ratio: float,
        **kwargs
    ):
        if not soup:
            soup = await self._async_get_soup(url=url, html=html, request_args=request_args)

        return self._get_result_by_func(
            func,
            url,
            html,
            soup,
            request_args,
            grouped,
            group_by_alias,
            unique,
            attr_fuzz_ratio,
            **kwargs
        )


    def _get_result_by_func(
        self,
        func: Callable,
        url: str,
        html: str,
        soup: BeautifulSoup,
        request_args: dict[str, Any],
        grouped: bool,
        group_by_alias: bool,
        unique: bool,
        attr_fuzz_ratio: float,
        **kwargs
    ):
        """
        - Purpose: Generic result processor
        - Features:
            1. Handles both grouped and ungrouped results
            2. Supports aliasing
            3. Manages result uniqueness
            4. Preserves order if needed
        """
        if not soup:
            soup = self._get_soup(url=url, html=html, request_args=request_args)

        keep_order = kwargs.get("keep_order", False)

        if group_by_alias or (keep_order and not grouped):
            for index, child in enumerate(soup.findChildren()):
                setattr(child, "child_index", index)

        result_list = []
        grouped_result = defaultdict(list)
        for stack in self.stack_list:
            if not url:
                url = stack.get("url", "")

            result = func(stack, soup, url, attr_fuzz_ratio, **kwargs)

            if not grouped and not group_by_alias:
                result_list += result
                continue

            group_id = stack.get("alias", "") if group_by_alias else stack["stack_id"]
            grouped_result[group_id] += result

        return self._clean_result(
            result_list, grouped_result, grouped, group_by_alias, unique, keep_order
        )

    @staticmethod
    def _clean_result(
        result_list: list, 
        grouped_result: defaultdict, 
        grouped: bool, 
        grouped_by_alias: bool, 
        unique: bool, 
        keep_order: bool
    ) -> list|dict:
        """
        - Purpose: Post-processes and formats results
        - Features:
            1. Deduplication
            2. Order preservation
            3. Grouping by rules or aliases
        """
        if not grouped and not grouped_by_alias:
            if unique is None:
                unique = True
            if keep_order:
                result_list = sorted(result_list, key=lambda x: x.index)
            result = [x.text for x in result_list]
            if unique:
                result = unique_hashable(result)
            return result

        for k, val in grouped_result.items():
            if grouped_by_alias:
                val = sorted(val, key=lambda x: x.index)
            val = [x.text for x in val]
            if unique:
                val = unique_hashable(val)
            grouped_result[k] = val

        return dict(grouped_result)


    def get_result_similar(
        self,
        url: Optional[str] = None,
        html: Optional[str] = None,
        soup: Optional[BeautifulSoup] = None,
        request_args: Optional[dict[str, Any]] = None,
        grouped: bool = False,
        group_by_alias: bool = False,
        unique: Optional[bool] = None,
        attr_fuzz_ratio: float = 1.0,
        keep_blank: bool = False,
        keep_order: bool = False,
        contain_sibling_leaves: bool = False,
    ) -> list|dict:
        """
        Gets similar results based on the previously learned rules.

        Args:
            url: URL of the target web page. Either url or html should be provided.
            html: An HTML string. Either url or html should be provided.
            soup: A BeautifulSoup object of the HTML.
            request_args: Additional parameters for the requests module (e.g., proxy, headers).
            grouped: If True, returns a dict with rule_ids as keys and scraped data as values.
            group_by_alias: If True, returns a dict with rule aliases as keys and scraped data as values.
            unique: If True, removes duplicates from the result list.
            attr_fuzz_ratio: Fuzziness ratio threshold for matching HTML tag attributes (0 to 1).
            keep_blank: If True, returns empty strings for missing values.
            keep_order: If True, maintains the order of results as they appear on the web page.
            contain_sibling_leaves: If True, includes sibling leaves of the wanted elements.

        Returns:
            A list of similar results scraped from the web page, or a dictionary if
            grouped or group_by_alias is True.
        """

        func = self._get_result_with_stack
        return self._get_result_by_func(
            func,
            url,
            html,
            soup,
            request_args,
            grouped,
            group_by_alias,
            unique,
            attr_fuzz_ratio,
            keep_blank=keep_blank,
            keep_order=keep_order,
            contain_sibling_leaves=contain_sibling_leaves,
        )

    async def async_get_result_exact(self,
        url: Optional[str] = None,
        html: Optional[str] = None,
        soup: Optional[BeautifulSoup] = None,
        request_args: Optional[dict[str, Any]] = None,
        grouped: bool = False,
        group_by_alias: bool = False,
        unique: Optional[bool] = None,
        attr_fuzz_ratio: float = 1.0,
        keep_blank: bool = False,
        ):
        func = self._get_result_with_stack_index_based
        return await self._async_get_result_by_func(
            func,
            url,
            html,
            soup,
            request_args,
            grouped,
            group_by_alias,
            unique,
            attr_fuzz_ratio,
            keep_blank=keep_blank,
        )

    async def async_get_result_similar(
        self,
        url: Optional[str] = None,
        html: Optional[str] = None,
        soup: Optional[BeautifulSoup] = None,
        request_args: Optional[dict[str, Any]] = None,
        grouped: bool = False,
        group_by_alias: bool = False,
        unique: Optional[bool] = None,
        attr_fuzz_ratio: float = 1.0,
        keep_blank: bool = False,
        keep_order: bool = False,
        contain_sibling_leaves: bool = False,
    ):
        func = self._get_result_with_stack
        return await self._async_get_result_by_func(
            func,
            url,
            html,
            soup,
            request_args,
            grouped,
            group_by_alias,
            unique,
            attr_fuzz_ratio,
            keep_blank=keep_blank,
            keep_order=keep_order,
            contain_sibling_leaves=contain_sibling_leaves,
        )

    def get_result_exact(
        self,
        url: Optional[str] = None,
        html: Optional[str] = None,
        soup: Optional[BeautifulSoup] = None,
        request_args: Optional[dict[str, Any]] = None,
        grouped: bool = False,
        group_by_alias: bool = False,
        unique: Optional[bool] = None,
        attr_fuzz_ratio: float = 1.0,
        keep_blank: bool = False,
    ):
        """
        Gets exact results based on the previously learned rules.

        Parameters:
        ----------
        url: str, optional
            URL of the target web page. You should either pass url or html or both.

        html: str, optional
            An HTML string can also be passed instead of URL.
                You should either pass url or html or both.

        request_args: dict[str, Any], optional
            A dictionary used to specify a set of additional request parameters used by requests
                module. You can specify proxy URLs, custom headers etc.

        grouped: bool, optional, defaults to False
            If set to True, the result will be a dictionary with the rule_ids as keys
                and a list of scraped data per rule as values.

        group_by_alias: bool, optional, defaults to False
            If set to True, the result will be a dictionary with the rule alias as keys
                and a list of scraped data per alias as values.

        unique: bool, optional, defaults to True for non grouped results and
                False for grouped results.
            If set to True, will remove duplicates from returned result list.

        attr_fuzz_ratio: float in range [0, 1], optional, defaults to 1.0
            The fuzziness ratio threshold for matching html tag attributes.

        keep_blank: bool, optional, defaults to False
            If set to True, missing values will be returned as empty strings.

        Returns:
        --------
        List of exact results scraped from the web page.
        Dictionary if grouped=True or group_by_alias=True.
        """

        func = self._get_result_with_stack_index_based
        return self._get_result_by_func(
            func,
            url,
            html,
            soup,
            request_args,
            grouped,
            group_by_alias,
            unique,
            attr_fuzz_ratio,
            keep_blank=keep_blank,
        )
    
    async def async_get_result(
        self,
        url: Optional[str] = None,
        html: Optional[str] = None,
        request_args: Optional[dict[str, Any]] = None,
        grouped: bool = False,
        group_by_alias: bool = False,
        unique: Optional[bool] = None,
        attr_fuzz_ratio: float = 1.0,
    ):
        soup = await self._async_get_soup(url=url, html=html, request_args=request_args)
        return self.get_result(url=url, 
                               html=html, 
                               request_args=request_args, 
                               grouped=grouped, 
                               group_by_alias=group_by_alias, 
                               unique=unique, 
                               attr_fuzz_ratio=attr_fuzz_ratio, 
                               soup=soup)

    def get_result(
        self,
        url: Optional[str] = None,
        html: Optional[str] = None,
        request_args: Optional[dict[str, Any]] = None,
        grouped: bool = False,
        group_by_alias: bool = False,
        unique: Optional[bool] = None,
        attr_fuzz_ratio: float = 1.0,
        soup: Optional[BeautifulSoup] = None
    ):
        """
        Gets similar and exact results based on the previously learned rules.

        Parameters:
        ----------
        url: str, optional
            URL of the target web page. You should either pass url or html or both.

        html: str, optional
            An HTML string can also be passed instead of URL.
                You should either pass url or html or both.

        request_args: dict[str, Any], optional
            A dictionary used to specify a set of additional request parameters used by requests
                module. You can specify proxy URLs, custom headers etc.

        grouped: bool, optional, defaults to False
            If set to True, the result will be dictionaries with the rule_ids as keys
                and a list of scraped data per rule as values.

        group_by_alias: bool, optional, defaults to False
            If set to True, the result will be a dictionary with the rule alias as keys
                and a list of scraped data per alias as values.

        unique: bool, optional, defaults to True for non grouped results and
                False for grouped results.
            If set to True, will remove duplicates from returned result list.

        attr_fuzz_ratio: float in range [0, 1], optional, defaults to 1.0
            The fuzziness ratio threshold for matching html tag attributes.

        Returns:
        --------
        Pair of (similar, exact) results.
        See get_result_similar and get_result_exact methods.
        """
        if not soup:
            soup = self._get_soup(url=url, html=html, request_args=request_args)

        args = dict(
            url=url,
            soup=soup,
            grouped=grouped,
            group_by_alias=group_by_alias,
            unique=unique,
            attr_fuzz_ratio=attr_fuzz_ratio,
        )
        similar = self.get_result_similar(**args)
        exact = self.get_result_exact(**args)
        return similar, exact

    def remove_rules(self, rules: list[Any]):
        """
        Removes a list of learned rules from stack_list.

        Parameters:
        ----------
        rules : list
            A list of rules to be removed

        Returns:
        --------
        None
        """

        self.stack_list = [x for x in self.stack_list if x["stack_id"] not in rules]

    def keep_rules(self, rules: list[Any]):
        """
        Removes all other rules except the specified ones.

        Parameters:
        ----------
        rules : list
            A list of rules to keep in stack_list and removing the rest.

        Returns:
        --------
        None
        """

        self.stack_list = [x for x in self.stack_list if x["stack_id"] in rules]

    def set_rule_aliases(self, rule_aliases: dict[str, Any]):
        """
        Sets the specified alias for each rule

        Parameters:
        ----------
        rule_aliases : dict
            A dictionary with keys of rule_id and values of alias

        Returns:
        --------
        None
        """

        id_to_stack = {stack["stack_id"]: stack for stack in self.stack_list}
        for rule_id, alias in rule_aliases.items():
            id_to_stack[rule_id]["alias"] = alias


    def generate_python_code(self):
        # deprecated
        print("This function is deprecated. Please use save() and load() instead.")


    def make_bs4_stacklist_from_playwright_stack_list(self):
        """
        Constructs a list of BeautifulSoup-compatible locators based on an existing Playwright stack_list.

        This method converts the Playwright-based stack_list to a format that can be used
        with BeautifulSoup for web scraping.

        Returns:
        --------
        list
            A list of dictionaries, each containing BeautifulSoup-compatible locators and attributes.
        """
        bs4_stack_list = []

        for stack in self.stack_list:
            bs4_stack = {
                'content': [],
                'wanted_attr': stack['wanted_attr'],
                'is_full_url': stack['is_full_url'],
                'is_non_rec_text': stack.get('is_non_rec_text', False),
                'alias': stack.get('alias', ''),
                'stack_id': stack['stack_id']
            }

            for locator in stack['locators']:
                tag_name, attrs = self._parse_playwright_locator(locator)
                bs4_stack['content'].append((tag_name, attrs))

            bs4_stack_list.append(bs4_stack)

        return bs4_stack_list


    def _parse_playwright_locator(self, locator):
        """
        Parses a Playwright locator string into a tag name and attributes dictionary.

        Args:
        -----
        locator : str
            A Playwright locator string (e.g., "div[class='example'][id='test']")

        Returns:
        --------
        tuple
            A tuple containing the tag name and a dictionary of attributes
        """
        import re

        tag_pattern = r'^(\w+)'
        attr_pattern = r'\[(\w+)=[\'"]([^\'"]+)[\'"]\]'

        tag_match = re.match(tag_pattern, locator)
        tag_name = tag_match.group(1) if tag_match else None

        attrs = {}
        for attr, value in re.findall(attr_pattern, locator):
            attrs[attr] = value

        return tag_name, attrs


    def make_playwright_stack_list_from_bs4_stack_list(self):
        """
        Constructs a list of Playwright-compatible locators based on the existing stack_list.

        This method converts the BeautifulSoup-based stack_list to a format that can be used
        with Playwright for web scraping.

        Returns:
        --------
        list
            A list of dictionaries, each containing Playwright-compatible locators and attributes.
        """
        playwright_stack_list = []

        for stack in self.stack_list:
            playwright_stack = {
                'locators': [],
                'wanted_attr': stack['wanted_attr'],
                'is_full_url': stack['is_full_url'],
                'is_non_rec_text': stack.get('is_non_rec_text', False),
                'alias': stack.get('alias', ''),
                'stack_id': stack['stack_id']
            }

            for item in stack['content']:
                tag_name = item[0]
                attributes = item[1]

                # Construct Playwright locator
                locator = f"{tag_name}"
                if attributes:
                    for attr, value in attributes.items():
                        if attr in ['class', 'id']:
                            locator += f"[{attr}='{value}']"
                        else:
                            locator += f"[{attr}='{value}']"

                playwright_stack['locators'].append(locator)

            playwright_stack_list.append(playwright_stack)

        return playwright_stack_list