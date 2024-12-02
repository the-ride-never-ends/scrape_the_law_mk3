from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
from datetime import datetime
import os
import re
import time
from time import time as time_
from typing import Any, Coroutine, Optional
import functools
from datetime import datetime


import aiohttp
import duckdb
from playwright.async_api import async_playwright


from enum import Enum
from uuid import UUID

from database.mysql_database import MySqlDatabase
from logger.logger import Logger
from config.config import PROJECT_ROOT, SELECT_BATCH_SIZE, RANDOM_SEED

from utils.shared.make_id import make_id
from utils.shared.get_formatted_datetime import get_formatted_datetime


from utils.shared.limiters.limiter import Limiter

from urllib.parse import urlparse


# List of patterns indicating JavaScript usage
JS_PATTERNS = [
    # Script tags
    r'<script\s+.*?src=',  # External script
    r'<script>',  # Inline script
    # Common JavaScript frameworks and libraries
    r'react', r'angular', r'vue', r'jquery', r'backbone', r'ember',
    # AJAX calls
    r'xmlhttprequest', r'fetch\(', r'\$\.ajax',
    # Event listeners
    r'addeventlistener\(',
    # DOM manipulation
    r'document\.getelem', r'document\.createelem',
    # Single-page application markers
    r'#!', r'pushstate\(', r'onpopstate',
    # JavaScript-based routing
    r'router', r'route\(',
    # Asynchronous loading
    r'async', r'defer',
    # Common JavaScript methods
    r'onload=', r'onclick=', r'onsubmit=',
    # JavaScript frameworks' specific patterns
    r'ng-', r'v-', r'data-react',
    # Dynamic content loading
    r'innerhtml', r'textcontent',
    # JavaScript-based form validation
    r'onsubmit=', r'validate\(',
    # Web Components
    r'customelements', r'shadowdom',
    # Modern JavaScript features
    r'const\s', r'let\s', r'=>', r'async\s+function',
    # JavaScript modules
    r'import\s+.*\s+from', r'export\s+(default)?',
    # Web Workers
    r'worker\(', r'postmessage\(',
    # WebSocket
    r'websocket\(',
    # LocalStorage or SessionStorage
    r'localstorage', r'sessionstorage',
]


class RateLimitExceededError(Exception):
    pass

class InvalidURLError(Exception):
    pass

class RobotsTxtViolationError(Exception):
    pass

class NetworkFailureError(Exception):
    pass

class ContentNotFound(Exception):
    pass


class Status(Enum):
    NEW = "new"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"

class DocumentType(Enum):
    HTML = "html"
    PDF = "pdf"
    OTHER = "other"

class SourceType(Enum):
    GOV = "gov" # Placeholder for any source.
    CITY_GOV = "city gov"
    COUNTY_GOV = "county gov"
    STATE_GOV = "state gov"
    NATIONAL_GOV = "national gov"
    CONTRACTED_REPO = "contracted repo"
    THIRD_PARTY_REPO = "third-party repo"
    OTHER = "other"

@dataclass
class SourceUrl:
    """
    A specific URL path under Domain, sub-domain, or URL path,
    along with associated metadata
    """
    source_id: UUID
    url: str
    source_type: SourceType
    is_active: bool
    is_domain: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self):
        if len(self.url) > 2200:
            raise ValueError("URL length cannot exceed 2200 characters")

@dataclass
class DocumentUrl:
    """
    A specific URL path under Domain, sub-domain, or URL path for a specific document,
    along with associated metadata
    """
    document_id: UUID
    source_id: UUID
    url: str
    last_scrape: datetime
    last_successful_scrape: datetime
    current_version_id: UUID
    status: Status
    priority: int
    document_type: DocumentType

    def __post_init__(self):
        if len(self.url) > 2200:
            raise ValueError("URL length cannot exceed 2200 characters")
        if not 1 <= self.priority <= 5:
            raise ValueError("Priority must be between 1 and 5")


@dataclass
class ScrapingResult:
    """
    Dataclass for scraping results.
    """
    job_id: UUID
    content: str|bytes
    content_type: DocumentType
    metadata: dict[str, Any]
    timestamp: datetime
    success: bool
    error: Optional[str] = None


@dataclass
class ErrorResult:
    job_id: UUID
    error_type: Exception
    error_message: str
    error_context: dict = None
    error_id: UUID = None
    occurred_at: datetime = None
    _times_retried: int = 0
    _is_resolved: bool = False

    def __post_init__(self):
        self.error_id = make_id()
        self.occurred_at = get_formatted_datetime()

    @property 
    def is_resolved(self):
        return self._is_resolved

    @is_resolved.setter
    def is_resolved(self, value: bool):
        if not isinstance(value, bool):
            raise ValueError("is_resolved must be a boolean value")
        self._is_resolved = value

    @property 
    def times_retried(self):
        return self._times_retried

    @is_resolved.setter
    def times_retried(self, value: int):
        if not isinstance(value, int):
            raise ValueError("times_retried must be a boolean value")
        self._times_retried = value


def determine_source_type(domain: str) -> SourceType:
    """
    Determine the source type based on the domain.
    This is a placeholder implementation and should be expanded based on your specific requirements.
    """
    contracted_repos = [
        "municode", # Municode
        "amlegal", # American Legal
        # General Code
        "ecode360", 
        "municipal.codes", 
        "codepublishing", 
    ]

    if any(repo in domain for repo in contracted_repos):
        return SourceType.CONTRACTED_REPO
    elif "lexisnexis" in domain:
        return SourceType.THIRD_PARTY_REPO
    elif "gov" in domain:
        return SourceType.GOV
    else:
        return SourceType.OTHER

from web_scraper.playwright.async_.async_playwright_scraper import AsyncPlaywrightScrapper

class AsyncWebScraperBase(AsyncPlaywrightScrapper):
    """
    Abstract base class for web scrapers.
    """
    def __init__(self, *args, configs: dict[str, Any], **kwargs):
        self.select_batch_size = SELECT_BATCH_SIZE
        self.configs = configs
        self.session = None
        self.supported_types: int = None
        self.num_workers: int = None
        self.max_retires: int = kwargs.pop("max_retries")
        self.headers: dict = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
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
        self.error_list: list = []
        super().__init__(*args, **kwargs)


    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize resources needed for scraping.
        """
        pass

			@abstractmethod
			def __aenter__(self):
						return await self

    @abstractmethod
    async def preprocess_url(self, url: DocumentUrl | SourceUrl ) -> DocumentUrl | SourceUrl:
        """
        Preprocess the URL before scraping.

        Args:
            url (Union[DocumentUrl, SourceUrl]): The URL to preprocess.

        Returns:
            Union[DocumentUrl, SourceUrl]: The preprocessed URL.

        Raises:
            InvalidURLError: If the URL format is invalid.
            RobotsTxtViolationError: If the URL violates robots.txt rules.
            RateLimitExceededError: If the rate limit for the source has been exceeded.

        Algorithm:
            For each URL in queue:
                1.1. Validate URL format
                1.2. Check robots.txt compliance
                1.3. Determine source type (Municode, LexisNexus, etc.)
                1.4. Load source-specific configuration
                1.5. Check rate limit status
        """

        # 1.1. Validate URL format
        parsed_url = urlparse(url.url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise InvalidURLError(f"Invalid URL format: {url.url}")

        # 1.2. Check robots.txt compliance
        await self.get_robot_rules()

        # 1.3. Determine source type
        source_type = determine_source_type(parsed_url.netloc)
        
        # 1.4. Load source-specific configuration
        if isinstance(url, SourceUrl):
            config = self.load_source_config(source_type)

        # 1.5. Check rate limit status
        if not self.check_rate_limit(source_type):
            raise RateLimitExceededError(f"Rate limit exceeded for source type: {source_type}")

        # Update the URL object with the determined source type and configuration
        if isinstance(url, SourceUrl):
            url.source_type = source_type
        else:
            pass # Since we already know the source type for documents, we can skip this.

        return url

    # TODO
    def load_source_config(self, source_type: SourceType) -> dict:
        """
        Load source-specific configuration.
        This is a placeholder implementation and should be expanded based on your specific requirements.
        """
        # In a real implementation, this might load from a configuration file or database
        return self.configs.get(source_type, {})

    # TODO
    def check_rate_limit(self, source_type: SourceType) -> bool:
        """
        Check if the rate limit for the given source type has been exceeded.
        This is a placeholder implementation and should be expanded based on your specific rate limiting logic.
        """
        # In a real implementation, this might check against a rate limiting service or database
        self.request_rate
        return True  # Always allow for now

    # TODO
    @abstractmethod
    async def process_content(self, result: ScrapingResult):
        """
        Process the content from a successful scraping result.

        For each successful response:
            3.1. Detect content type
            3.2. Generate content hash
            3.3. Store raw content and metadata
            3.4. If content is HTML:
                    Parse DOM
                    Extract relevant sections
                    Store metadata
            3.5. If content is PDF/other:
                    Save to temporary storage
                    Pass to appropriate content processor
        """
        if not result.success:
            Logger.error(f"Failed to process content for job {result.job_id}: {result.error}")
            return

        # 3.1. Detect content type
        content_type = result.content_type

        # 3.2. If content is HTML
        if content_type == DocumentType.HTML:
            try:
                # Parse DOM
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(result.content, 'html.parser')

                # Extract relevant sections (example: all paragraph texts)
                relevant_content = ' '.join([p.text for p in soup.find_all('p')])

                # Store metadata
                result.metadata['extracted_text'] = relevant_content
                result.metadata['title'] = soup.title.string if soup.title else ''

            except Exception as e:
                Logger.error(f"Error processing HTML content for job {result.job_id}: {str(e)}")

        # 3.3. If content is PDF/other
        elif content_type in [DocumentType.PDF, DocumentType.OTHER]:
            
            try:
                # Save to temporary storage
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{content_type.value}") as temp_file:
                    temp_file.write(result.content)
                    temp_path = temp_file.name

                # Pass to appropriate content processor
                if content_type == DocumentType.PDF:
                    # Example: Extract text from PDF
                    import PyPDF2
                    with open(temp_path, 'rb') as pdf_file:
                        reader = PyPDF2.PdfReader(pdf_file)
                        text = ''
                        for page in reader.pages:
                            text += page.extract_text()
                    result.metadata['extracted_text'] = text
                else:
                    # For other types, you might want to implement specific processing logic
                    result.metadata['file_path'] = temp_path

            except Exception as e:
                Logger.error(f"Error processing {content_type.value} content for job {result.job_id}: {str(e)}")

        # 3.4. Generate content hash
        import hashlib
        content_hash = hashlib.sha256(result.content).hexdigest()
        result.metadata['content_hash'] = content_hash

        # 3.5. Store raw content and metadata
        try:
            # This is a placeholder. You should implement your own storage logic.
            # For example, you might want to use a database or file system.
            await self.store_content_and_metadata(result)
        except Exception as e:
            Logger.error(f"Error storing content and metadata for job {result.job_id}: {str(e)}")

    async def store_content_and_metadata(self, result: ScrapingResult):
        """
        Store the raw content and metadata in the appropriate storage system.
        This method should be implemented according to your specific storage requirements.
        """
        # This is a placeholder implementation. Replace with your actual storage logic.
        Logger.info(f"Storing content and metadata for job {result.job_id}")
        # Example: You might want to store in a database
        # await database.store_scraping_result(result)
        pass


    # TODO
    @abstractmethod
    @self.handle_errors
    async def process_url(self, inp: DocumentUrl | SourceUrl) -> str|bytes:
        """
        inp: input from asyncio.Queue
        """
        url = inp
        await self.preprocess_url(url)
        scraping_result = await self.execute_scrape(url)
        await self.process_content(scraping_result)


    # TODO
    @abstractmethod
    async def execute_scrape(self, inp: DocumentUrl | SourceUrl) -> ScrapingResult:
        """
        Execute the scraping process for a given URL.

        While URL queue not empty AND within resource limits:
            2.1. Initialize HTTP session with appropriate headers
            2.2. Apply rate limiting delay if needed
            2.3. Send HTTP request with timeout
            2.4. If response successful:
                Store response headers
                Check content type
                Buffer response content
            2.4. If JavaScript required:
                Initialize headless browser
                Execute JavaScript
                Wait for dynamic content
                Extract final state
        """
        job_id = make_id()
        timestamp = datetime.now()

        try:
            # 2.1. Initialize HTTP session with appropriate headers
            async with aiohttp.ClientSession(headers=self.headers) as session:
                # 2.2. Apply rate limiting delay if needed
                await self.apply_rate_limit(inp.url)
                
                # 2.3. Send HTTP request with timeout
                async with session.get(inp.url, timeout=30) as response:
                    # 2.4. If response successful:
                    if response.status == 200:
                        # Store response headers
                        headers = dict(response.headers)

                        # Check content type
                        content_type = response.headers.get('Content-Type', '')
                        
                        if 'text/html' in content_type:
                            # Buffer response content
                            content = await response.text()
                            doc_type = DocumentType.HTML

                        elif 'application/pdf' in content_type:
                            content = await response.read()
                            doc_type = DocumentType.PDF

                        else:
                            content = await response.read()
                            doc_type = DocumentType.OTHER

                    elif response.status == 403 or response.status == 406:
                        
                        # Assume refused requests or forbidden requests require javascript of some kind.
                        # 2.4. Check if JavaScript is required:
                        async with async_playwright() as pw_instance:

                            # Initialize headless browser
                            scraper = await AsyncPlaywrightScrapper.start(inp.url, pw_instance)

                            # Go to the URL again and wait for the content to load.
                            content = await scraper.navigate_to(inp.url, headers=self.headers)

                            # Execute JavaScript and wait for dynamic content
                            if self.requires_javascript():
                                pass

                            # Extract final state
                            doc_type = DocumentType.HTML
                                
                        metadata = {
                            'url': inp.url,
                            'headers': headers,
                            'content_type': content_type,
                        }
                        
                        return ScrapingResult(
                            job_id=job_id,
                            content=content,
                            content_type=doc_type,
                            metadata=metadata,
                            timestamp=timestamp,
                            success=True
                        )
                    else:
                        raise ContentNotFound(f"HTTP {response.status}: Content not found for {inp.url}")

        except asyncio.TimeoutError:
            return ScrapingResult(
                job_id=job_id,
                content="",
                content_type=DocumentType.OTHER,
                metadata={},
                timestamp=timestamp,
                success=False,
                error="Request timed out"
            )
        except Exception as e:
            return ScrapingResult(
                job_id=job_id,
                content="",
                content_type=DocumentType.OTHER,
                metadata={},
                timestamp=timestamp,
                success=False,
                error=str(e)
            )


    def requires_javascript(self, content: str) -> bool:
        """
        Check if the content requires JavaScript execution by looking for various
        tell-tale signs of JavaScript usage.
        """
        # Convert content to lowercase for case-insensitive matching
        content_lower = content.lower()

        # Check for the presence of any JavaScript patterns
        for pattern in JS_PATTERNS:
            if re.search(pattern, content_lower):
                return True

        # Check for suspicious empty elements that might be populated by JavaScript
        empty_elements = re.findall(r'<(?:div|span|p|section|article)\s+[^>]*>\s*</(?:div|span|p|section|article)>', content)
        if len(empty_elements) > 5:  # Arbitrary threshold, adjust as needed
            return True

        # Check for elements with JavaScript-related attributes
        js_attributes = ['data-', 'ng-', 'v-', 'x-', '@']
        for attr in js_attributes:
            if attr in content_lower:
                return True

        return False


    @abstractmethod
    async def scrape_url(self, url: DocumentUrl|SourceUrl) -> ScrapingResult:
        """
        Scrape content from a single URL. 
        How exactly to scrape the URL depends on the domain and/or the scrape configs.
        """
        pass

    @abstractmethod
    async def create_list_of_document_urls(self) -> list[DocumentUrl]:
        """
        Get a list of document URLs from the MySQL server.
        Algorithm:
            1. Set a batch size (e.g., 100 URLs per batch)
            2. Initialize an empty list to store the URLs
            3. Set up a database connection
            4. Execute a SELECT query to fetch URLs from the Documents table:
                - Order by priority (highest first) and last_scrape (oldest first)
                - Limit the result to the batch size
                - Filter for URLs that are due for scraping (e.g., last_scrape older than a certain threshold)
            5. Fetch the results and convert them to DocumentUrl objects
            6. Add the fetched URLs to the list
            7. Update the status of the fetched URLs to 'processing' in the database
            8. Close the database connection
            9. Return the list of DocumentUrl objects
        """
        pass


    # TODO
    def handle_errors(self, name: str, func: Coroutine) -> ErrorResult | Any:
        """
        On error:
            4.1. Categorize error type:
                Network failure
                Rate limit exceeded
                Authentication required
                Content not found
                Parsing error
            4.2. Log error details
            4.3. Update URL status
            4.4. Implement retry strategy:
                If retries < max_retries:
                    Add to retry queue with backoff
                Else:
                    Mark as failed
                    Report to error handler
        """
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):

            retries = 0
            exp_backoff = 2
            # Instantiate the error result class as None, since 
            error_result = None

            while retries < self.max_retries:
                if retries >= 1:
                    asyncio.sleep(2 ** exp_backoff) # Square the back-off for every max-retry.
                try:
                    result = await func(*args, **kwargs)
                    if error_result is not None:
                        error_result.is_resolved = True
                    return result
                except Exception as e:
                    # Create the error result.
                    error_context = {"func": func, "args": args, "kwargs": kwargs}
                    if retries == 0: # Spawn the error_result object if it's the first error.
                        error_result = ErrorResult(job_id=make_id(), error_type=Exception, error_context=error_context)

                    # Do retries for the appropriate errors
                    if isinstance(e, (NetworkFailureError, RateLimitExceededError, ContentNotFound,)):
                        # func.logger # Access the worker's logger.
                        print(f"{e.__qualname__} encountered: {e}\n Retrying...")
                        retries += 1
                        error_result.times_retried = retries
                    else:
                        self.error_list.append(error_result)
                        break

                # All retries failed.
                return error_result

            return wrapper

    # TODO
    @abstractmethod
    async def create_list_of_urls(self, table: str) -> list[SourceUrl] | list[DocumentUrl]:
        """
        Get a list of source URLs from the MySQL server.

        Algorithm:
            1. Set a batch size (e.g., 100 URLs per batch)
            2. Initialize an empty list to store the URLs
            3. Set up a database connection
            4. Execute a SELECT query to fetch URLs from the Sources table:
                - Order by RANDOM_SEED
                - Limit the result to the batch size
                - Filter for URLs that are already in the Documents Table
            5. Fetch the results and convert them to DocumentUrl objects
            6. Add the fetched URLs to the list
            7. Update the status of the fetched URLs to 'processing' in the database
            8. Close the database connection
            9. Return the list of SourceUrl objects
        """

        sql_command = """
        SELECT * FROM Sources
        WHERE is_active = TRUE AND updated_at IS NULL
        ORDER BY RAND({RANDOM_SEED})
        LIMIT {SELECT_BATCH_SIZE}
        """

        # Define variables based on the input table
        url_dataclass = SourceUrl if table == "Sources" else DocumentUrl
        file_name = "create_list_of_source_urls" if table == "Sources" else "create_list_of_document_urls"
        file_path = os.path.join(PROJECT_ROOT, "sql_scripts", "mysql", f"{file_name}.sql")
        args = {"random_seed": RANDOM_SEED, "insert_batch_size": SELECT_BATCH_SIZE,}

        # Get the data from the database, and assign it to the classes
        async with await MySqlDatabase(database="scrape_the_law") as db:
            db: MySqlDatabase
            results: list[dict] = await db.async_execute_sql_file(file_path, args=args, return_dict=True)

        return [url_dataclass(**result) for result in results]


    # TODO
    async def create_tasks_for_scrape(self, 
                                      urls_list: list[SourceUrl] | list[DocumentUrl]
                                      ) -> None:
        """
        See: https://docs.python.org/3/library/asyncio-queue.html#asyncio.QueueShutDown
        """
        limiter = Limiter(semaphore=2)

        await limiter.run_async_many_in_queue(
            inputs = urls_list,
            func=self._execute_scrape
        )


    @abstractmethod
    async def cleanup(self) -> None:
        """
        Clean up resources after scraping.
        """
        pass

    async def __aenter__(self):
        """
        Context manager entry.
        """
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit.
        """
        await self.cleanup()