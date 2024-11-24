# Program: scrape_the_law
Version: 0.1.1
Author: Kyle Rose, Claude 3.5 Sonnet

## Table of Contents
1. Problem Definition
- 1.1 Objective
- 1.2 Seed Dataset Specifications
- 1.3 Legal Text Source Specifications
- 1.4 Input Type Specifications
2. Requirements Matrix
3. System Requirements
4. Constraints
5. Implementation Phases
6. Dependencies

# 1. Problem Definition


## 1.1 Objective
Build a web scraping system to collect municipal legal codes from US cities/counties and store them in a structured SQL database. The system will:
- Extract legal codes from official government or government-contracted websites and databases.
- Parse and standardize raw content into tabular data with metadata
- Store in SQL database with proper relationships and versioning
- Maintain version history and track code updates/amendments
- Handle different website structures and content formats


## 1.2 Seed Dataset Specifications
| Attribute        | Specification                                                            | Bounds/Constraints                      |
|------------------|--------------------------------------------------------------------------|-----------------------------------------|
| Description      | Table containing all national incorporated places and counties in US¹    | Active, non-tribal communities only     |
| Format           | CSV file, MySQL Database                                                 | N/A                                     |
| Size             | 23,089 data points²                                                      | Legal codes must be available online    |
| Delivery Methods | - API endpoint<br>- File download                                        | File types: Restful API, XLSX, CSV      |
| Source Authority | - State of Iowa<br>- U.S. Geological Survey                              | N/A                                     |
- 1: For US government definition of census-designated places, see: https://www2.census.gov/geo/pdfs/reference/GARM/Ch9GARM.pdf, accessed 11/23/2024
- 2: Source: https://data.iowa.gov/Boundaries/National-Incorporated-Places-and-Counties/djvt-gf3t/about_data, accessed 11/23/2024


## 1.3 Legal Datum Source Specifications
| Attribute        | Specification                                          | Bounds/Constraints                       |
|------------------|--------------------------------------------------------|------------------------------------------|
| Description      | Datum containing legal information                     | Processable by an LLM                    |
| Format           | Various, see section 1.4 Input Type Specifications     | Must be convertible to UTF-8             |
| Size             | Arbitrary Length                                       | Source document must be available online |
| Delivery Methods | - Direct extraction via web-scraping<br> - API endpoint<br>- Terminal input<br>- File download  | See section 1.4: Input Type Specifications           |
| Source Authority | Government or government-contracted websites           | Must be verifiable as a source authority |
- 1: For examples, see: https://guides.loc.gov/municipal-codes/current-municipal-codes, accessed 11/23/2024


### 1.4 Input Type Specifications
| Source Type | Characteristics                                             | Challenges                                                        |
|-------------|-------------------------------------------------------------|-------------------------------------------------------------------|
| HTML        | - Dynamic loading<br>- Nested navigation<br>- Mixed content | - JavaScript rendering<br>- Session handling<br>- Rate limiting   |
| PDF         | - Scanned docs<br>- Text PDFs<br>- Mixed formats            | - OCR support<br>- Layout parsing<br>- Table and graph extraction |
| DOCX, DOC   | - Format rendering issues<br>- Embedded images and tables<br>- Version compatibility | - Parsing complex formatting<br>- Extracting metadata<br>- Handling track changes |
| XLSX, CSV   | - Mixed Formats<br>- Different Use Cases<br>- Multiple sheets | - Parsing formulas<br>- Handling merged cells<br>- Interpreting data types |
| PHP, etc.   | - Server-side rendering<br>- Dynamic content generation<br>- Database interactions | - Handling server-side logic<br>- Session management<br>- Security considerations |
| XML, JSON APIs | - Structured data format<br>- Authentication requirements<br>- Rate limits | - API version changes<br>- Error handling<br>- Data synchronization |
| Website Structures | - Municode<br>- American Legal<br>- CodePublishing<br>- LexisNexus<br>- Various Government Websites<br>| - Different structures of varying complexity<br>- Authentication<br>- Terms of service |


## 1.4 Input Processing Requirements
### 1.4.1 Source Validation
   - Websites/Documents accessibile by permanent URL (e.g. Internet Archive, Libgen).
   - Codes are only scraped from verified sources.
   - Websites are government, government-affiliated, or government contracted.
   - Monthly update frequency

### 1.4.2 Content Extraction Validation
   - Complete code hierarchy captured
   - No missing sections
   - Images/tables parsed and stored properly
   - Ensure extraction quality from difficult-to-parse documents like flat PDFs, presentational XLSX, etc. 

### 1.4.3 Data Cleaning Validation
   - Document artifacts removed or corrected
   - Proper section numbering
   - Consistent formatting
   - Reference integrity
   - Flag and store overlapping or conflicting laws.
   - Audits via manually comparing raw to processed documents, as determined by random sampling.

### 1.4.4 Storage Requirements
   - SQL schema for hierarchical legal code structure
   - Version control for amendments
   - Metadata tracking (source URL, last updated, etc.)
   - Efficient querying capabilities
   - Storage optimization for text data.

### 1.4.5 Robustness Requirements
   - Respectful crawling (rate limits, robots.txt).
   - Handle site downtime/failures gracefully.
   - Process different content formats (HTML, PDF, DOC, XLSX).
   - Scale across thousands of jurisdictions, potential for arbitrary number of jurisdictions.

### 1.4.5 Version Control Requirements
   - Full database refresh annually.
   - Monthly updates on a per text basis.
   - Checksums for downloaded and processed documents via SHA256 hash.
   - Amendments linked via metadata (source hashes, page numbers, creation dates, etc.)
   - Accuracy audits via random sampling.
   - Version control system for tracking changes in laws over time.
   - Update notifications: Alert system for users when relevant laws are updated by comparing versions gathered over time.

### 1.4.6 Performance Requirements

6. Error handling: 
   - Implement a robust system to flag, log, and report errors.
   - Errors include Network, Query, Cleaning, and Validation Errors
7. Legal compliance
   - Respect copyright laws and terms of service. 
   - Follow ethical web scraping practices. 


### 1.5 Success Criteria

### 1.5.1 Minimum Viable Product (MVP)
| Feature            | Description                          | Success Criteria                                                                                          |
|--------------------|--------------------------------------|-----------------------------------------------------------------------------------------------------------|
| Basic Scraping Functionality | Fully scrape 1 legal repository     | - Successfully makes both docs <br>- Meets quality metrics (Section 1.5.2)<br>- Completes in < 5 minutes |
| Document Type Support    | HTML, PDF            | - Correctly processes English text <br>- Rejects non-English inputs                                       |
| Persistant Document Storage         | .txt and .md file processing         | - Successfully reads both file types <br>- Handles UTF-8 encoding                                         |
| Error Handling     | Input validation and error reporting | - Catches and reports common errors <br>- Provides clear error messages                                   |
| Legal Compliance     | Input validation and error reporting | - Catches and reports common errors <br>- Provides clear error messages                                   |


## 1.6 Scope Definition
## 1.6.1 Explicitly Out of Scope
| Feature                      | Description                                                                                                |
|------------------------------|------------------------------------------------------------------------------------------------------------|
| Real-time Documentation      | - Live document updates <br>- Websocket connections <br>- Real-time collaboration                          |
| Advanced Features            | - Code generation <br>- Test case generation <br>- Automated implementation <br>- Custom template creation |
| Integration Features         | - CI/CD pipeline integration <br>- IDE plugins <br>- Direct repository management                          |
| Authentication/Authorization | - User management <br>- Role-based access <br>- Multi-tenant support                                       |





## 1.6 Output
### 1.6.1 Ouput Specification
| Output Type      | Format               | Performance Target |
|------------------|----------------------|--------------------|
| API Response     | JSON/XML/YAML/TXT    | <200ms response    |
| Processed Codes  | Structured Database  | Monthly updates    |
| Version History  | Git-like changelog   | Unlimited history  |


## 1.7 Core Constraints
- Rate limiting: Max 1 request/second per jurisdiction
- Storage: Expected 500GB/year growth **TODO Needs to be estimated. This seems like it's too large**
- Compliance: Must maintain original text alongside cleaned version
- Availability: 99.9% uptime for API


## 1.8 Use cases:
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





# 2. Requirements Matrix






















## 1.6 Primary Use Cases
### 1.6.1. Legal Research
- Search across jurisdictions
- Compare versions over time
### 1.6.2. Compliance Monitoring
- Track changes in specific areas
- Receive notifications of updates
### 1.6.3. Data Analysis
- Cross-jurisdictional analysis
- Trend identification
### 1.6.4. LLM Fodder
- 



## 1.4 Outputs

### 14.1 Output Specifications

# 1. Get codes from LexisNexus (3,200 codes)
# - 1.1 Make Chrome extension to scrape the pages you visit TODO See if it can be HTML instead of PDF
# - 1.2 Go to law library and run the script
# 2. Scrape Municode (3,528 codes)
# - 2.1 Figure out API
# - 2.2 Scrape via API
# 3. Scrape American Legal (2,180 codes) TODO Ditto API
# 4. Scrape General Code (1,601 codes) TODO Ditto API
# 5. Get all the other websites (4,304)
# - 5.1 General Crawler.