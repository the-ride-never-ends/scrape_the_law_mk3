
# Program: scrape_the_law

1. Problem definition
2. High-level architecture
3. Data structures
4. Algorithms
5. Function/method signatures
6. Error handling
7. Testing strategy
8. Code organization
9. Naming conventions
10. External dependencies
11. Performance considerations - TODO
12. Scalability - TODO
13. Security considerations - TODO
14. Documentation needs - TODO










# 1. Problem Definition
- Objective: Retrieve, store, and maintain text of all local legal codes in the US.
- Languages: Python, MySQL, JavaScript
- Input:
   - Push of a button.
Outputs: A MySQL database of all local legal codes in the US related to the input datapoint. The ultimate variable "legal_text” is in plain text.








## Constraints:
1. Data Integrity:
   - Only primary/official sources (e.g. government websites, contracted law repository websites).
   - Publicly accessible online.
   - Text must be archived with a third party (e.g. Internet Archive, Libgen).
2. Scalability:
   - Handle and store millions or more pages of legal text and associated metadata.
   - Metadata must be sufficient for rigorous academic citation.
   - Extensible beyond local laws if needed.
3. Performance:
   - Complete full retrieval and cleaning cycle monthly.
   - Maximum time for retrieval and cleaning: 14 days.
   - Cost optimization: Minimize cost per character of output text so that the dataset is produced as cheaply as possible.
4. Reliability: 
   - Size: Dataset must cover over 50% of the US population. Preferably, more than all US legal code databases combined.
   - Factual Accuracy: Codes must be factually accurate, up-to-date, and trustworthy.
5. Maintainability: 
   - Design for monthly execution and updates.
   - Extensible to weekly or daily updates if needed.
6. Robustness:
   - Rate limiting of scraping and search engine usage.
   - Alert user to unsuccessful data gathering attempts.
7. Output format: Human-readable plaintext.


## Scope:
1. Geographic Coverage:
   - Included: Incorporated communities (local (city, township) and county laws).
   - Excluded: Federal and State-level legal codes, option for state-level legal codes in the future.
2. Time Frame
   - Focus on current year's laws (2024)
   - Quarterly updates for significant changes.
   - Historical laws are currently excluded, but support for them may be added in the future. 
3. Language
   - Primary focus on English
   - Other languages are currently ignored unless otherwise specified.
   - Architecture allowing for future multilingual support.
4. Content Completeness
   - Flag and store overlapping or conflicting laws.
   - Flag gaps in data so that they can be found through alternative methods or sources.
5. Data validation:
   - Take random sample of 385 content pages and qualitatively judge them against the raw source documents.
6. Error handling: 
   - Implement a robust system to flag, log, and report errors.
   - Errors include Network, Query, Cleaning, and Validation Errors
7. Legal compliance
   - Respect copyright laws and terms of service. 
   - Follow ethical web scraping practices. 


## Data Integrity and Verification:
   - Checksums for downloaded and processed documents via SHA256 hash.
   - Cross-reference data with multiple sources where possible.
   - Periodic audits via random sampling.
   - Version control system for tracking changes in laws over time.
## Scalability Plans
   - Design database schema to accommodate multiple data points.
   - Modular code structure for easy addition of new data sources.
   - Plan for distributed processing capabilities for handling increased load.
## Update Process:
   - Full database refresh: Annually
   - Incremental updates: Monthly checks for significant law changes
   - Version control: Maintain historical versions of laws for tracking changes.
   - Update notifications: Alert system for users when relevant laws are updated by comparing versions gathered over time.


## Use cases:
1. Constructing a dataset of legal codes for extracting legal datapoint manually or via LLM.
   - Key Metric: Size of Dataset
2. Legal researchers: Analyze trends in local legislation across jurisdictions.
   - Key Metric: Accuracy of Cleaned Text to Source Text
3. Legal professionals: Quick reference for local laws on specific topics.
   - Key Metric: Accuracy of Cleaned Text to Source Text
4. ML researchers: Train models on local legal language and structures.
   - Key Metric: Size
5. Policy analysts: Compare local laws across different regions.
   - Key Metric: Accuracy of Cleaned Text to Source Text.


# 2. High-Level Architecture
1. **Input Processing Module 'input.py'**
   - Validates and sanitizes the input datapoint
   - Handles potential future expansion to multiple data points
   - **COMPLETE**

2. **Search Engine Interface 'search.py'**
   - Manages API connections to search engines
   - Implements rate limiting and error handling
   - Stores search results and metadata in the ‘locations’ and ‘searches’ tables, respectively
   - Already implemented via “google_seach.py” and the “PlaywrightGoogleLinkSearch” class.
   - **COMPLETE BUT NEEDS FINE-TUNING**

3. **Query Generator 'query.py'**
   - Generates search engine queries based on input datapoint and location information
   - Implements query formatting and construction
   - Handles query hashing for efficient storage and retrieval
   - Stores generated queries and their metadata in a MySQL database.
   - Provides functionality to retrieve existing queries from the database
   - **COMPLETE**

4. **Scraping Module 'scrape.py'**
   - Retrieves URLs from legal code databases (e.g. Municode, American Legal, General Code.)
   - URLs include legal code versions, legal code URLs, and city website URLs.
   - Uses proxies and other techniques to bypass rate limiting and bot detection
   - Stores URLs from scraped content to the MySQL database.
   - **Municode is Functional, but can be optimized.**
   - **American Legal and General Code need to be considered.**

4. **Archiving Module 'archive.py'**
   - Saves search result URLs to the Internet Archive
   - Implements ethical scraping practices and respects robots.txt
   - Stores archived url metadata in 'ia_url_metadata' tables
   - **WIP, but IA is being hacked so I need another way to archive things.**

5. **Web Scraping Module 'Waybackup subproccess'**
   - Retrieves URLs from the Internet Archive based on search results
   - Handles different input formats (HTML, PDF, etc.)
   - Stores raw content and metadata in “doc_content” and “doc_metadata” tables, respectively.
   - Retrieving URLs is already handled in a separate python program/subprocess “waybackup”
   - **COMPLETE BUT NEEDS FINE-TUNING**

6. **Content Extraction and Cleaning Module 'clean.py'**
   - Extracts text from various document formats
   - Cleans and normalizes the extracted text.
   - Stores processed content in 'doc_content' table
   - **HTML2TEXT and Various Other**

7. **Metadata Management Module 'metadata.py'**
   - Extracts and manages metadata from documents
   - Metadata includes all information necessary to produce a rigorous academic citation
   - 7.1 Author if possible
   - 7.2 Source Name (HTML page title, PDF title)
   - 7.3  
   - Stores document metadata in 'doc_metadata' table

8. **Database Management System 'database.py'**
   - Handles all database operations (CRUD)
   - Implements database schema and relations
   - Manages data integrity and consistency
   - **COMPLETE**

10. **Error Handling and Logging System 'logger.py'**
   - Centralized error handling for all modules
   - Comprehensive logging for debugging and auditing
   - **COMPLETE**

11. **Data Validation and Integrity Module 'validate.py'**
   - Implements checksums for downloaded documents
   - Manages periodic audits and cross-referencing
   - **IN FUTURES FOLDER**

12. **Scalability Management Module 'scale.py'**
   - Handles distributed processing (if implemented)
   - Manages resources for increased load
   - **IN FUTURES FOLDER**

13. **API/Interface Module 'api.py'**
   - Provides access to the collected data for various use cases
   - Implements security and access control
   - Largely unnecessary, as the data will be accessed via MySQL database by different programs.
   - **IN FUTURES FOLDER**

14. **Scheduler 'schedule.py'**
   - Manages the execution of full retrieval cycles and updates
   - Coordinates the operation of other modules
   - **IN FUTURES FOLDER**


# 3. Data Structures
## 1. In-Memory Data Structures:
   - Pandas DataFrames:
      - Primary structure for moving and manipulating data.
   - Python base types
      - Sets, Queues, Dictionaries, etc.
   - Dataclasses that match SQLSCHEMA.md
## 2. Database Structures
   - Input/out variables are defined here.
   - See Datbase Schema in SQLSCHEMA.md
## 3. File Structures
   - YAML config files, "config.yaml" and "private_config.yaml"
   - Log files: Structured plaintext files, with option to output JSON.
   - Screenshots: JPEG screenshots to validate web scraping.


# 4. Algorithms
# 4.1 Search Query Generation
1. Input:
   - Datapoint (e.g. "sales tax")
   - Location information (GNIS id, place name, state code, domain name)
   - Source URL (Municode, American Legal, or General Code, domain name)
- Process:
  1. Sanitize and validate input datapoint.
      - Remove special characters, normalize spacing.
      - Logic for including synonyms or related terms (e.g. sales tax vs sales and use tax) if applicable.
  2. Retrieve location information from 'locations' table in MySQL database.
      - Source URLs are pre-generated using commonly observed patterns.
  3. Construct search query using datapoint, source URL, and location.
      - Optimize each query for Google's search engine as default.
      - Ex: 'site:https://codelibrary.amlegal.com/codes/kingcoveak/latest/kingcove_ak/ "sales tax" OR "sales and use tax"'
  4. Generate query hash for efficient storage and retrieval.
- Output: Formatted search query and associated metadata.

# 4.2 Web Search
- Input:
   - Search queries from Search Query Generation
   - location information (GNIS id, place name, state code, domain name)
   - A specific search engine (e.g. Google Search) or an API for it.
- Process:
   1. Check if a query has already been run within the last year.
   2. If it has not been run in the past year but has been run before, check the number of results it returned.
   3. Run the query through the chosen search engine it was not run in the last year and returned results OR if it hasn't been run before.
   4. Count the number of results.
   5. If the query produced results, save the URLs. Otherwise, just note that it produced no results.
   6. Generate url hash for efficient storage and retrieval.
- Output: Search result URLs and associated metadata (time queried, number of results).

# 4.3 Web Scraping
- Input: Search results URLs
- Process:
   1. Check if URL is already archived.
   2. If not archived or if the archive is not from the current year, submit URL to Internet Archive.
      - Rate limit of 1 URL upload per second.
   3. Retrieve content from Internet Archive.
      - Check if a specific URL path needs to have elements loaded first. If it does, wait for them to load.
      - Rate limit of 1 URL download per second.
   4. Handle different input formats (HTML, PDF, etc.).
      - Directly download HTML, PDF, and doc files.
      - Note other file types (e.g. php, csv, etc.)
   5. Extract raw content.
   6. Store content metadata in 'doc_metadata' table on MySQL database.
   7. Store raw content in 'doc_content' table on MySQL database if it's under a certain size, otherwise stream it in futher steps.
- Output: Raw content and associated metadata.

# 4.4 Content Extraction and Cleaning
- Input: Raw content from various document formats
- Process:
  1. Detect document format.
  2. Extract text using appropriate method for each format.
      - For HTML, process with Beautiful Soup or other HTML processors.
      - For PDF, use Jinja to convert it if it's not flat, otherwise use OCR via Pytesseract, PDFMiner, or vision-capable LLMs.
      - Other formats (e.g., Word, Excel, php) can be converted to HTML for extraction or extracted directly. 
  3. Remove tags, scripts, and other non-content elements.
  4. Normalize text (e.g. consistent spacing and line breaks, character encoding).
  5. Identify and extract relevant sections related to the datapoint via word matching, regex, or LLMs (e.g. BERT, T5, etc.).
  6. Apply any specific cleaning rules for legal text on a case-by-case basis.
- Output: Cleaned and normalized text content.

# 4.5 Update Detection
- Input: Existing content and newly scraped content
- Process:
  1. Compare checksums of existing and new content.
  2. If checksums differ, perform detailed comparison.
  3. Identify added, modified, and deleted sections.
  4. Generate change log.
  5. Update database with new content and change information.
- Output: Updated content, change log, and update notifications.


## 4.1.1 Specific details for Search Query Generation:
1. Query formats for different search engines:
   - Google search syntax (e.g., use of quotation marks, site: operator).
   - Bing search syntax (e.g., filetype: operator).
   - DuckDuckGo syntax (e.g., using bangs for site-specific searches).
   - Handling special characters in queries.
   - Constructing Boolean queries (AND, OR, NOT operators).
   - Using advanced search operators (inurl:, intitle:, etc.).

2. Handling synonyms or related terms:
   - Maintaining a thesaurus of legal terms and common synonyms.
   - Implementing fuzzy matching for similar terms.
   - Using word embeddings to find semantically related terms.
   - Handling acronyms and their full forms (e.g., "sales tax" vs "ST").
   - Considering regional variations in terminology.

3. Incorporating location-specific information:
   - Formatting city names (e.g., "New York City" vs "NYC").
   - Handling hyphenated city names.
   - Including state abbreviations and full names.
   - Using zip codes or county names for more specific searches.
   - Handling special administrative divisions (e.g., boroughs, parishes).
   - Incorporating landmark names or colloquial area names.

4. Avoiding search engine detection and blocking:
   - Implementing dynamic IP rotation.
   - Using proxy servers or VPNs.
   - Randomizing user agents.
   - Adding delays between queries (with random intervals).
   - Mimicking human search patterns (e.g., occasional misspellings, varied query lengths).
   - Distributing queries across multiple search engines.
   - Implementing CAPTCHA solving capabilities.

5. Query construction and optimization:
   - Prioritizing keywords based on relevance.
   - Balancing query specificity and recall.
   - Handling long-tail queries for niche legal topics.
   - Implementing query expansion techniques.
   - Using domain-specific search operators (e.g., site:.gov for government websites).
   - Constructing queries to target specific document types (e.g., "filetype:pdf").

6. Query storage and management:
   - Generating unique identifiers for each query.
   - Storing query history for auditing and optimization.
   - Implementing a caching mechanism for frequent queries.
   - Managing query quotas for different search engines.
   - Tracking query performance metrics (e.g., number of relevant results).

7. Error handling and edge cases:
   - Handling queries with no results.
   - Dealing with misspelled location names or datapoints.
   - Managing queries that exceed maximum length limits.
   - Handling special characters or non-ASCII input.
   - Implementing fallback strategies for failed queries.

8. Compliance and ethical considerations:
   - Respecting search engine terms of service.
   - Implementing appropriate delays between queries.
   - Avoiding overloading smaller municipal websites.
   - Considering fair use and copyright implications of queries.

9. Performance optimization:
   - Implementing parallel query generation for multiple locations.
   - Using efficient data structures for storing and retrieving query components.
   - Optimizing string operations for query construction.
   - Implementing batch processing for large-scale query generation.

10. Integration with other system components:
   - Interfacing with the database for retrieving location data.
   - Passing generated queries to the web scraping module.
   - Providing feedback to the input processing module for query refinement.
   - Integrating with logging and monitoring systems.


# 5. Function/method signatures
   - Detailed documentation on functions and method signatures is provided within the source code and will be omitted here for brevity.
   - Sphinx documentation will be generated for the project on final release.

# 6. Error handling
   - Error handling will be handled by Python's built in exception handling mechanisms (try-except blocks, raising, checksums, etc.)
   - Detailed implementation is on a per-function basis and will be omitted here for brevity.

# 7. Testing strategy
   - Linear pipeline, where each module is tested sequentially before integration.
   - Progress is "saved" via uploading output data to the database or outputting to a file (CSV, screenshot, etc.).
   - 100% code coverage will be achieved through unit testing using the pytest library and running the program seqentially through each module.

# 8. Code organization
   - The project is organized based on the modules in 'High-Level Architecture'.
   - Each module has a main class and its own utility functions in the 'utils' directory.
   - Manual subprocesses that only have to be run once have their own directory 'manual'.

# 9. Naming conventions
   1. Python conforms to PEP8 naming conventions.
      - Variables and functions are named use lowercase with underscores.
      - Classes use CamelCase.
      - Constants and global variables use ALL_CAPS.
      - Private variables and methods are named using a single underscore prefix.
      - 3rd party libraries are imported using staandard naming conventions (e.g. import pandas as pd).
      - Utility file namings follow the same conventions as their primary function or class (e.g. AsyncPlaywrightScrapper class is in AsyncPlaywrightScrapper.py)
      - Critical orchestration files are one word, undercase (e.g. database.py)
      - **TODO: Standardization of formats**
   2. MySQL follows standard SQL naming conventions.
      - Tables and input and output variables are named using lowercase with underscores.
      - Commands are written in ALL CAPS.


# 10. External dependencies
   - This project makes extensive use of Pandas, Aiomysql, and Playwright.
   - See requirements.txt for all 3rd party libraries.
   - NOTE: Not all libraries are currently used, and will be culled on final release.


11. Performance considerations - TODO
12. Scalability - TODO
13. Security considerations - TODO
14. Documentation needs - TODO












| Primary Needs                    | Data Type                  |
|----------------------------------|----------------------------|
| Accessibility compliance         | Binary                     |
| Accuracy of legal text           | Real-Valued Additive       |
| Amendment tracking               | Software Feature           |
| API accessibility                | Binary                     |
| API stability                    | Binary                     |
| Building codes                   | Categorical                |
| Bulk downloads                   | Binary                     |
| Change tracking                  | Software Feature           |
| Citation standards               | Categorical                |
| Clean training data              | Software Feature           |
| Code relationships               | Other                      |
| Complete metadata                | Software Feature           |
| Compliance guidance              | Software Feature           |
| Compliance tracking              | Software Feature           |
| Compliance verification          | Software Feature           |
| Consistent formatting            | Software Feature           |
| Cost impact analysis             | Real-Valued Additive       |
| Cross-agency coordination        | Other                      |
| Cross-jurisdiction comparison    | Other                      |
| Data format consistency          | Categorical                |
| Data standardization             | Process                    |
| Development guidelines           | Categorical                |
| Discrimination detection         | Software Feature           |
| Documentation quality            | Ordinal                    |
| Environmental regulations        | Categorical                |
| Equal protection analysis        | Other                      |
| Fast access to relevant codes    | Real-Valued Multiplicative |
| Ground truth annotations         | Software Feature           |
| Historical analysis              | Time-series                |
| Historical context               | Time-series                |
| Impact assessments               | Categorical                |
| Jurisdiction comparison          | Software Feature           |
| Jurisdiction coverage            | Categorical                |
| Land use regulations             | Categorical                |
| Local variation tracking         | Software Feature           |
| Pattern identification           | Other                      |
| Permit requirements              | Categorical                |
| Plain language summaries         | Software Feature           |
| Policy impact analysis           | Software Feature           |
| Public accessibility             | Binary                     |
| Quick fact verification          | Software Feature           |
| Regulatory compliance            | Other                      |
| Research datasets                | Other                      |
| Risk assessment                  | Other                      |
| Simplified compliance guides     | Software Feature           |
| Source attribution               | Software Feature           |
| Teaching materials               | Other                      |
| Transparency metrics             | Ordinal                    |
| Version history                  | Count                      |
| Zoning regulations               | Categorical                |













| Stakeholder | Primary Needs | Data Type: Statistical | Metric | Target | Measurement Method |
|-------------|---------------|------------------------|--------|--------|--------|



| Civil Rights Organizations | Accessibility compliance | Binary | WCAG 2.1 Level AA compliance (Yes/No)|
| Lawyers | Accuracy of legal text | Real-Valued Additive | Error rate per 1000 words |
| Lawmakers | Amendment tracking | Feature | Feature is present |
| Social Science Researchers | API accessibility | Real-Valued Additive | Uptime percentage over rolling 30-day period |
| Software Developers | API stability | Real-Valued Additive | Percentage of public access uptime over rolling 30-day period |
| Real Estate Developers | Building codes | Real-Valued Additive | Coverage Rate (%) |
| Social Science Researchers | Bulk downloads | Feature | Feature is present |
| Anti-corruption Activists | Change tracking | Feature | Feature is present |
| Academic Institutions | Citation standards | Real-Valued Additive | Percentage of correct citations per style |
| AI Researchers | Clean training data | Feature | Feature is present |
| Lawmakers | Code relationships | Other | Percentage of possible connections implemented |
| Legal Scholars | Complete metadata | Real-Valued Additive | Metadata Coverage Rate (%) |
| Business Owners | Compliance guidance | Feature | Feature is present |
| Environmental Groups | Compliance tracking | Feature | Feature is present |
| Insurance Companies | Compliance verification | Feature | Feature is present |
| AI Researchers | Consistent formatting | Feature | Feature is present |
| Small Business Associations | Cost impact analysis | Feature | Feature is present |
| Government Agencies | Cross-agency coordination | Other | Percentage of cross-agency references implemented |
| Lawmakers | Cross-jurisdiction comparison | Other | Percentage of required cross-references implemented |
| Software Developers | Data format consistency | Real-Valued Additive | Coverage Rate (%) |
| Social Science Researchers | Data standardization | Feature | Feature is present |
| City Planners | Development guidelines | Real-Valued Additive | Coverage Rate (%) |
| Civil Rights Organizations | Discrimination detection | Feature | Feature is present |
| Software Developers | Documentation quality | Ordinal | 1-5 scale with defined criteria for each level |
| City Planners | Environmental regulations | Real-Valued Additive | Coverage Rate (%) |
| Environmental Groups | Environmental regulations | Real-Valued Additive | Coverage Rate (%) |
| Civil Rights Organizations | Equal protection analysis | Real-Valued Additive | Coverage Rate (%) |
| Lawyers | Fast access to relevant codes | Binary | Average response time in milliseconds under <200ms (yes/no) |
| AI Researchers | Ground truth annotations | Feature | Feature is present |
| Legal Scholars | Historical analysis | Count | Number of Code Versions Available |
| Journalists | Historical context | Real-Valued Additive | Coverage Rate (%) |
| Environmental Groups | Impact assessments | Feature | Feature is present |
| Insurance Companies | Jurisdiction comparison | Feature | Feature is present |
| Business Owners | Jurisdiction coverage | Real-Valued Additive | Coverage Rate (%) |
| Real Estate Developers | Land use regulations | Real-Valued Additive | Coverage Rate (%) |
| Small Business Associations | Local variation tracking | Feature | Feature is present |
| Legal Scholars | Pattern identification | Time-series | Rate of change in Coverage Rate (%) |
| Real Estate Developers | Permit requirements | Real-Valued Additive | Coverage Rate (%) |
| Business Owners | Plain language summaries | Feature | Feature is present |
| Government Agencies | Policy impact analysis | Feature | Feature is present |
| Anti-corruption Activists | Public accessibility | Binary | 24/7 public access availability (Yes/No) |
| Journalists | Quick fact verification | Feature | Feature is present |
| Government Agencies | Regulatory compliance | Binary | Automated compliance validation system operational (Yes/No) |
| Academic Institutions | Research datasets | Feature | Feature is present |
| Insurance Companies | Risk assessment | Ordinal | 1-5 scale with defined risk criteria |
| Small Business Associations | Simplified compliance guides | Feature | Feature is present |
| Journalists | Source attribution | Real-Valued Additive | Coverage Rate (%) |
| Academic Institutions | Teaching materials | Feature | Feature is present |
| Anti-corruption Activists | Transparency metrics | Feature | Feature is present |
| Lawyers | Version history | Feature | Feature is present |
| City Planners | Zoning regulations | Real-Valued Additive | Coverage Rate (%) |