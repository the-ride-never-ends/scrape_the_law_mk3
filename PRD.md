




# Program: make_canned_documentation
Version: 0.1.1

## Table of Contents
1. Problem Definition
2. Requirements Matrix
3. System Requirements
4. Constraints
5. Implementation Phases
6. Dependencies

# 1. Problem Definition


## 1.1 Objective
Build a web scraping system to collect municipal legal codes from US cities/counties and store them in a structured SQL database. The system will:
- Extract legal codes from official government or government-contracted websites and databases.
- Parse and standardize raw content into structured data
- Store in SQL database with proper relationships and versioning
- Maintain version history and track code updates/amendments
- Handle different website structures and content formats


## 1.2 Seed Dataset Specifications
| Attribute        | Specification                                                            | Bounds/Constraints                      |
|------------------|--------------------------------------------------------------------------|-----------------------------------------|
| Description      | Table containing all national incorporated places and counties in US¹    | Active, non-tribal communities only     |
| Format           | c                                        | Must be convertible to UTF-8            |
| Size             | 23,089 data points²                                                      | Legal codes must be available online    |
| Delivery Methods | - API endpoint<br>- File download                                        | File types: Restful API, .xlsx, .csv    |
| Source Authority | - State of Iowa<br>- U.S. Geological Survey                              | N/A                                     |
- 1: For US government definition of census-designated places, see: https://www2.census.gov/geo/pdfs/reference/GARM/Ch9GARM.pdf, accessed 11/23/2024
- 2: Source: https://data.iowa.gov/Boundaries/National-Incorporated-Places-and-Counties/djvt-gf3t/about_data, accessed 11/23/2024


## 1.2 Legal Text Source Specifications
| Attribute        | Specification                                          | Bounds/Constraints                      |
|------------------|--------------------------------------------------------|-----------------------------------------|
| Description      | Table containing all census-designated places in US    | Incorporated communities only           |
| Format           | Tabular data from a MySQL database                     | Must be convertible to UTF-8            |
| Size             | 23,089 (19,734 incorporated) data points*              | Legal codes must be available online    |
| Delivery Methods | - API endpoint<br>- Terminal input<br>- File download  | See section 1.3: Input Types         |
| Source Authority | Government or government-contracted websites           | Must be verifiable as a source authority |
-* For examples of what these are, see: https://guides.loc.gov/municipal-codes/current-municipal-codes, accessed 11/23/2024


### 1.3 Input Types
| Source Type | Characteristics                                             | Challenges                                                      |
|-------------|-------------------------------------------------------------|-----------------------------------------------------------------|
| HTML               | - Dynamic loading<br>- Nested navigation<br>- Mixed content | - JavaScript rendering<br>- Session handling<br>- Rate limiting |
| PDF                | - Scanned docs<br>- Text PDFs<br>- Mixed formats       | - OCR support<br>- Layout parsing<br>- Table and graph extraction    |
| docx               |
| xlsx, csv          |
| php, etc.          |
| Website Structures | - Municode<br>- American Legal<br>- CodePublishing<br>- LexisNexus| - Different structures<br>- Authentication<br>- Terms of service |


## 1.4 Input Processing Requirements
### 1.4.1 Source Validation
   - Websites/Documents accessibile by permanent URL
   - Content completeness
   - Navigation structure
   - Monthly update frequency

### 1.4.2 Content Extraction Validation
   - Complete code hierarchy captured
   - No missing sections
   - Images/tables parsed and stored properly
   - PDF, presentational xlsx text extraction quality

### 1.4.3 Data Cleaning Validation
   - Document artifacts removed
   - Proper section numbering
   - Consistent formatting
   - Reference integrity

### 1.4.4 Storage Requirements
   - SQL schema for hierarchical legal code structure
   - Version control for amendments
   - Metadata tracking (source URL, last updated, etc.)
   - Efficient querying capabilities
   - Storage optimization for text data

### 1.4.5 Processing Constraints
   - Respectful crawling (rate limits, robots.txt)
   - Handle site downtime/failures gracefully
   - Process different content formats (HTML, PDF, DOC, XLSX)
   - Scale across thousands of jurisdictions, potential to tens of thousands.


























## 1.4 Output
### 1.4.1 Ouput Specification
| Output Type      | Format               | Performance Target |
|------------------|----------------------|--------------------|
| API Response     | JSON/XML/YAML/TXT    | <200ms response    |
| Processed Codes  | Structured Database  | Monthly updates    |
| Version History  | Git-like changelog   | Unlimited history  |


## 1.5 Core Constraints
- Rate limiting: Max 1 request/second per jurisdiction
- Storage: Expected 500GB/year growth **TODO Needs to be estimated. This seems like it's too largs**
- Compliance: Must maintain original text alongside cleaned version
- Availability: 99.9% uptime for API


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
| Attribute        | Specification                                       | Bounds/Constraints                                      |
|------------------|-----------------------------------------------------|---------------------------------------------------------|
| Description      | Software documentation files                        | - Min: 5 Core Docs (P0)<br>- Max: 10 Extended Docs (P1) |
| Content          | Technical documentation based on input description  | See Section 1.4.3 'Output Content Requirements'         |
| Format           | Plain text, UTF-8 encoded                           | See Section 1.4.3 'Output Format Requirements'          |
| Size             | Variable                                            | - Min: 20480 tokens<br>- Max: 40960 tokens              |
| Language         | Primary: English                                    | Support for non-English outputs                         |
| Delivery Methods | - API endpoint<br>- File download                   | File types: .txt, .json, .md                            |















# 1. Get codes from LexisNexus (3,200 codes)
# - 1.1 Make Chrome extension to scrape the pages you visit TODO See if it can be HTML instead of PDF
# - 1.2 Go to law library and run the script
# 2. Scrape Municode (3,528 codes)
# - 2.1 Figure out API
# - 2.2 Scrape via API
# 3. Scrape American Legal (2,180 codes) TODO Ditto API
# 4. Scrape General Code (1,601 codes) TODO Ditto API
# 5. Get all the other websites
# - 5.1 General Crawler.