# Program: scrape_the_law_mk3
**Version: 0.1.1**<br>
**Authors: Kyle Rose, Claude 3.5 Sonnet**

## Table of Contents
1. Problem Definition
- 1.1 Objective
- 1.2 Seed Dataset Specifications
- 1.3 Legal Text Source Specifications
- 1.4 Input Type Specifications
2. Requirements Matrix TODO 
3. System Requirements TODO
4. Constraints TODO
5. Implementation Phases TODO
6. Dependencies TODO


## NOTE: Termonology Shorthand
For the sake of brevity, the following shorthand will be used where it does not fundamentally change the intent or meaning of the text.
| Termonology                        | Shorthand                  |
|------------------------------------|----------------------------|
| 'incorporated places and counties' | 'cities'.                  |
| 'legal text', 'legal document'     | 'law'                      |
| 'documents'                        | 'docs' when not in header. |
| 'gigabytes'                        | 'GB'                       |
| 'large language model'             | 'LLM'                      |
| 'number'                           | '#'                        |
| 'specifications'                   | 'specs' when not in header |
| 'information'                      | 'info' when not in header  |
| 'requirements'                     | 'reqs' when not in header  |
| 'repository'                       | 'repo'                     |


# 1. Problem Definition

## 1.1 Problem Statement
Per the US Library of Congress, there currently does not exist a single repository for all US municipal codes.¹ This reduces government transparency, increases the cost of legal compliance, and prevents the automation of legal research.
- 1: See: https://guides.loc.gov/municipal-codes/current-municipal-codes, accessed 11/24/2024

## 1.2 Objective
Build a web scraping system to collect municipal legal codes from US cities/counties and store them in a structured database. The system will:
- Extract legal documents from official government or government-contracted websites and databases.
- Parse and standardize raw content into tabular data with metadata
- Store in a database with proper relationships and versioning
- Maintain version history and track code updates/amendments
- Handle different website structures and content formats

## 1.3 Success Metrics by Stakeholder Type

### 1.3.1 Legal/Government Stakeholders
| Stakeholder | Primary Needs | Metric | Target | Measurement Method |
|-------------|--------------|---------|---------|-------------------|
| Lawyers | - Fast access to relevant codes<br>- Accuracy of legal text<br>- Version history | - Search response time<br>- Text accuracy rate<br>- Version tracking completeness | - < 2s search time<br>- 99.9% accuracy<br>- 100% version coverage | - API response timing<br>- Random sample audit<br>- Version history validation |
| Lawmakers | - Cross-jurisdiction comparisons<br>- Amendment tracking<br>- Code relationships | - Cross-reference completeness<br>- Amendment detection rate<br>- Relationship mapping accuracy | - 95% reference coverage<br>- 98% amendment detection<br>- 90% relationship accuracy | - Coverage analysis<br>- Change detection audit<br>- Graph validation |
| Government Agencies | - Cross-agency coordination<br>- Policy impact analysis<br>- Regulatory compliance | - Inter-agency reference tracking<br>- Policy change impacts<br>- Compliance overlap detection | - 95% agency coverage<br>- < 48hr impact analysis<br>- 98% overlap detection | - Agency validation<br>- Change impact tracking<br>- Overlap analysis tools |
| City Planners | - Zoning regulations<br>- Development guidelines<br>- Environmental regulations | - Spatial data integration<br>- Code visualization accuracy<br>- Environmental compliance tracking | - 90% spatial integration<br>- 95% visualization accuracy<br>- 100% env. tracking | - GIS validation<br>- Visual audit<br>- Compliance checks |


### 1.3.2 Business/Industry Stakeholders
| Stakeholder | Primary Needs | Metric | Target | Measurement Method |
|-------------|--------------|---------|---------|-------------------|
| Business Owners | - Compliance guidance<br>- Plain language summaries<br>- Jurisdiction coverage | - Jurisdictional coverage<br>- Update timeliness<br>- Code accessibility | - 80% jurisdiction coverage<br>- < 30 day update lag<br>- > 95% availability | - Coverage tracking<br>- Update monitoring<br>- Uptime monitoring |
| Real Estate Developers | - Land use regulations<br>- Building codes<br>- Permit requirements | - Regulation completeness<br>- Code update tracking<br>- Permit requirement accuracy | - 98% coverage<br>- < 24hr updates<br>- 100% requirement accuracy | - Coverage audit<br>- Update monitoring<br>- Requirement validation |
| Insurance Companies | - Risk assessment<br>- Compliance verification<br>- Jurisdiction comparison | - Risk factor extraction<br>- Compliance tracking<br>- Cross-jurisdiction analysis | - 95% risk coverage<br>- 100% compliance tracking<br>- 90% comparison accuracy | - Risk validation<br>- Compliance audit<br>- Analysis verification |
| Small Business Associations | - Simplified compliance guides<br>- Cost impact analysis<br>- Local variation tracking | - Guide clarity<br>- Cost assessment accuracy<br>- Variation detection | - 90% clarity rating<br>- 95% cost accuracy<br>- 98% variation detection | - User feedback<br>- Cost validation<br>- Variation audit |


### 1.3.3 Research/Academic Stakeholders
| Stakeholder | Primary Needs | Metric | Target | Measurement Method |
|-------------|--------------|---------|---------|-------------------|
| Legal Scholars | - Historical analysis<br>- Pattern identification<br>- Complete metadata | - Historical depth<br>- Metadata completeness<br>- Citation accuracy | - 10 year history<br>- 98% metadata coverage<br>- 99% citation accuracy | - Historical audit<br>- Metadata validation<br>- Citation checking |
| Social Science Researchers | - Data standardization<br>- API accessibility<br>- Bulk downloads | - Data format consistency<br>- API uptime<br>- Download completeness | - 100% standardization<br>- 99.9% API uptime<br>- 100% download success | - Format validation<br>- Uptime monitoring<br>- Download verification |
| Academic Institutions | - Research datasets<br>- Teaching materials<br>- Citation standards | - Dataset completeness<br>- Educational usefulness<br>- Citation accuracy | - 99% completeness<br>- 90% usefulness rating<br>- 100% citation accuracy | - Dataset validation<br>- User surveys<br>- Citation checks |


### 1.3.4 Public Interest/Advocacy Stakeholders
| Stakeholder | Primary Needs | Metric | Target | Measurement Method |
|-------------|---------------|--------|--------|--------------------|
| Anti-corruption Activists | - Transparency metrics<br>- Change tracking<br>- Public accessibility | - Change detection rate<br>- Public access rate<br>- Update transparency | - 100% change tracking<br>- 100% public access<br>- < 24hr update notice | - Change log audit<br>- Access monitoring<br>- Update timing tracking |
| Civil Rights Organizations | - Discrimination detection<br>- Accessibility compliance<br>- Equal protection analysis | - Bias detection rate<br>- ADA compliance<br>- Protection coverage | - 95% detection rate<br>- 100% ADA compliance<br>- 100% coverage | - Bias analysis<br>- Compliance check<br>- Coverage audit |
| Environmental Groups | - Environmental regulations<br>- Impact assessments<br>- Compliance tracking | - Environmental code coverage<br>- Assessment completeness<br>- Violation tracking | - 100% env. coverage<br>- 95% assessment coverage<br>- 100% violation tracking | - Coverage analysis<br>- Assessment audit<br>- Violation monitoring |
| Journalists | - Quick fact verification<br>- Historical context<br>- Source attribution | - Search accuracy<br>- Historical coverage<br>- Citation completeness | - 99% search precision<br>- 10 year history<br>- 100% attribution | - Search testing<br>- Timeline validation<br>- Citation audit |


### 1.3.5 Technical Stakeholders
| Stakeholder | Primary Needs | Metric | Target | Measurement Method |
|-------------|--------------|---------|---------|-------------------|
| Software Developers | - API stability<br>- Documentation quality<br>- Data format consistency | - API versioning<br>- Doc completeness<br>- Schema validation | - 99.9% API stability<br>- 100% doc coverage<br>- 100% schema compliance | - Version monitoring<br>- Doc coverage audit<br>- Schema validation |
| AI Researchers | - Clean training data<br>- Consistent formatting<br>- Ground truth annotations | - Data cleaning quality<br>- Format standardization<br>- Annotation accuracy | - 99.9% data cleanliness<br>- 100% format compliance<br>- 98% annotation accuracy | - Data quality audit<br>- Format validation<br>- Annotation verification |


### 1.4 Global Success Metrics
| Category      | Metric                         | Minimum Target      | Optimal Target      | Measurement Method            |
|---------------|--------------------------------|---------------------|---------------------|-------------------------------|
| Coverage      | % of US municipalities covered | 50%                 | 95%                 | Geographic coverage analysis  |
| Accuracy      | Text accuracy vs. source       | 99%                 | 99.99%              | Random sample comparison      |
| Freshness     | Update lag time                | < 30 days           | < 7 days            | Update timestamp analysis     |
| Availability  | System uptime                  | 99%                 | 99.99%              | Continuous monitoring         |
| Performance   | Average query response time    | < 2s                | < 200ms             | API response timing           |
| Completeness  | Code section coverage          | 95%                 | 99.99%              | Section validation            |
| Transparency  | Source attribution rate        | 100%                | 100%                | Metadata audit                |
| Consistency   | Format standardization         | 95%                 | 99.99%              | Schema validation             |
| Scalability   | Data growth handling           | 20% annual increase | 50% annual increase | System performance monitoring |
| Reliability   | Error rate in data processing  | < 1%                | < 0.1%              | Error log analysis            |


## 1.5 Seed Dataset Specifications
| Attribute        | Specification                                                            | Bounds/Constraints                      |
|------------------|--------------------------------------------------------------------------|-----------------------------------------|
| Description      | Table with all national incorporated places and counties in US¹          | Active, non-tribal communities only     |
| Format           | CSV file, MySQL Database                                                 | N/A                                     |
| Size             | 22,899 data points²                                                      | Legal codes must be available online    |
| Delivery Methods | - API endpoint<br>- File download                                        | File types: Restful API, XLSX, CSV      |
| Source Authority | - State of Iowa<br>- U.S. Geological Survey                              | N/A                                     |
- 1: For US government definition of census-designated places, see: https://www2.census.gov/geo/pdfs/reference/GARM/Ch9GARM.pdf, accessed 11/23/2024
- 2: Source: https://data.iowa.gov/Boundaries/National-Incorporated-Places-and-Counties/djvt-gf3t/about_data, accessed 11/23/2024




## 1.7 Legal Document Source Specifications
| Attribute        | Specification                                          | Bounds/Constraints                       |
|------------------|--------------------------------------------------------|------------------------------------------|
| Description      | Docs with legal info                                   | Directly usable by an LLM                    |
| Format           | See section 1.4 'Input Type Specifications'            | Convertible to UTF-8 plaintext |
| Size             | Size in gigabytes                                      | Easily storable to disk |
| Delivery Methods | - Direct extraction via scraping<br> - API endpoint<br>- File download  | See section 1.4: Input Type Specifications           |
| Availability     |                                                        | Sources for docs are publically available online |
| Source Authority | Government or government-contracted websites           | Must be verifiable as a source authority |
- 1: For examples, see: https://guides.loc.gov/municipal-codes/current-municipal-codes, accessed 11/23/2024


## 1.8 Inputs
### 1.8.1 Input Type Specifications
| Source Type | Characteristics                                             | Challenges                                                        |
|-------------|-------------------------------------------------------------|-------------------------------------------------------------------|
| HTML        | - Dynamic loading<br>- Nested navigation<br>- Mixed media content | - JavaScript rendering<br>- Session handling<br>- Rate limiting   |
| PDF         | - Scanned/flat formats<br>- Text PDFs<br>- Mixed media content            | - OCR for parsing flat files<br>- Layout parsing<br>- Table and graph extraction |
| DOCX, DOC   | - Word-specific formatting<br>- Embedded images and tables<br>| - Parsing complex formatting<br>- Extracting metadata<br>- Tracking changes |
| XLSX, CSV   | - Diverse Formats<br>- Different Use Cases<br>- Multiple sheets<br>- Mixed media content | - Parsing formulas<br>- Handling merged cells<br>- Interpreting data types<br>- Table and graph extraction |
| PHP, etc.   | - Server-side rendering<br>- Dynamic content generation<br>- Database interactions | - Handling server-side logic<br>- Session management<br>- Security considerations |
| XML, JSON APIs | - Structured data format<br>- Authentication requirements<br>- Rate limits | - API version changes<br>- Error handling<br>- Data synchronization |
| GIS, Maps   | - Server-side rendering<br>- Dynamic content generation<br>- Parsing purely visual data<br>- Parsing spatial data | - Handling server-side logic<br>- Session management<br>- Security considerations |
| JPEG, PNG, etc. | | |
| Powerpoint | | |
| Website Structures | - Municode<br>- American Legal<br>- CodePublishing<br>- LexisNexus<br>- Various Government Websites<br>| - Different structures of varying complexity<br>- Authentication<br>- Terms of service |


## 1.8.2 Input Processing Requirements
### 1.8.2.1 Source Validation
   - Website/Doc sources accessibile by permanent, third-party URL (e.g. Internet Archive, Libgen).
   - Docs are only scraped from government, government-affiliated, or government contracted sources.
   - Monthly update frequency

### 1.8.2.2 Content Extraction Validation
   - Complete code hierarchy captured
   - No missing sections
   - Images/tables parsed and stored properly
   - Ensure extraction quality from difficult-to-parse docs like flat PDFs, presentational XLSX, etc. 

### 1.8.2.3 Data Cleaning Validation
   - Docs artifacts removed or corrected
   - Proper section numbering
   - Consistent formatting
   - Flag and store metadata on overlapping or conflicting Docs.
   - Option to perform manual audits by comparing randomly sampled raw and processed Docs formats.

### 1.8.2.4 Storage Requirements
   - Detailed SQL schema for hierarchical legal code structure
   - Version control for amendments
   - Metadata tracking (source URL, last updated, etc.)
   - Efficient querying capabilities
   - Storage optimization for text data.

### 1.8.2.5 Version Control Requirements
   - Full database refresh annually.
   - Monthly updates on a per text basis.
   - Checksums for downloaded and processed datum via SHA256 hash.
   - Amendments linked via metadata (source hashes, page #, creation dates, etc.)
   - Accuracy audits via random sampling.
   - Version control system for tracking changes in laws over time.
   - Update notifications: Alert system for users when relevant laws are updated by comparing versions gathered over time.

### 1.8.2.6 Robustness Requirements
   - Respectful crawling (rate limits, robots.txt).
   - Handle site downtime/failures gracefully.
   - System to flag, log, and report errors in any part of the process, specifically Network, Query, Cleaning, and Validation Errors.
   - Process different content formats (HTML, PDF, DOC, XLSX).
   - Scale across thousands of jurisdictions, potential for arbitrary # of jurisdictions.

### 1.8.2.7 Performance Requirements ( per Section 1.5.1 Minimum Viable Product)
   - Extraction of all codes from a repo in under 1 week
   - Parallel scraping support
   - CPU Usage: 1 Core
   - Memory Usage: 4 GBs
   - Database Query Performance: 2 GBs
   - API response times: <= 1 second


### 1.5 Success Criteria
### 1.5.1 Minimum Viable Product (MVP)
| Feature                        | Description                          | Minimum Success Criteria | Optimal Success Criteria |
|--------------------------------|--------------------------------------|--------------------------|--------------------------|
| Scraping Functionality         | Fully scrape 1 law repo              |  Download all raw versions legal docs for each city on the repo |- Download all repos | <br>- Completes in < 1 week<br> |
| Docs Type Support              | Extraction, cleaning, and validation of law docs | -  Support extraction, validation, and cleaning for HTML, text PDFs <br>- Flags non-textual docs such as graphs, tables, and images |
| Persistant Docs Storage        | Database of raw and cleaned Docs | - Efficiently stores plain-text copies of HTML and PDF Docs <br>- Handles UTF-8 encoding |
| Docs Extraction Rate           | # of docs scraped per hour | 5 docs per hour. | 100 docs per hour. |
| Docs Conversion Error Rate     | Errors in Docs extraction, cleaning, and validation. |- Minimum: 90% <br> - Optimal: 100%
| Error Handling                 | Input extraction, validation and error reporting | - Catches and reports common errors <br>- Provides clear error messages                                   |
| Legal Compliance               | Alert user to legal notices from stakeholders | - Logs and alerts user to legal notices <br> - Automated take-down measures <br>                                  |


### 1.5.2 MVP Timeline
| Feature                    | Phase # | Completion Date | Acceptance Criteria                                              | Status   |
|----------------------------|---------|-----------------|------------------------------------------------------------------|----------|
| **DROP DEAD DATE**         | N/A     | **12/31/2024**  | All minimum/acceptance completed                                 | NOT DONE |
| Core Documentation         | 0       | 11/30/2024      | PRD, Architecture, Database Schema, Algorithims docs complete    | NOT DONE |
| Scraping Functionality     | 1       | 12/8/2024       | Download all raw versions legal docs for each city on the repo   | NOT DONE |
| Doc Type Support           | 1       | 12/8/2024       | Support extraction, validation, and cleaning for HTML, text PDFs | NOT DONE |
| Doc Extraction Rate        | 2       | 12/15/2024      | 5 docs per minute                                                | NOT DONE |
| Doc Conversion Error Rate  | 2       | 12/15/2024      | < 10% for all errors, across all docs                            | NOT DONE |
| Persistant Docs Storage    | 3       | 12/22/2024      | All tables in database are defined, in-place, and storing info   | NOT DONE |
| Error Handling             | 3       | 12/22/2024      | Catch and report common errors                                   | NOT DONE |
| Legal Compliance           | 4       | 12/31/2024      | Alert user to legal notices from stakeholders                    | NOT DONE |


## 1.6 Scope Definition
### 1.6.1 Explicitly Out of Scope
| Feature                      | Description                                                                                                |
|------------------------------|------------------------------------------------------------------------------------------------------------|
| Real-time Gathering          | - Live Docs updates <br>- Websocket connections <br>- Real-time collaboration                          |
| Advanced Features            | - Data Extraction <br>- Real-time interaction  <br>- Automated implementation <br>- Custom template creation |
| Integration Features         | - CI/CD pipeline integration <br>- IDE plugins <br>- Direct repo management                          |
| Authentication/Authorization | - User management <br>- Role-based access <br>- Multi-tenant support                                       |


## 1.7 Output
### 1.7.1 Ouput Specifications
| Description       | Format               | Performance Target                    |
|-------------------|----------------------|---------------------------------------|
| API Response      | JSON/XML/YAML/TXT    |- <200ms response<br>- 99.9% uptime    |
| Unprocessed Codes | MySQL Database       | 20 GB on Disk <br>                    | 
| Processed Codes   | MySQL Database       | 10 GB on Disk <br>                    |
| Version History   | MySQL Database       | 12 Months of Changes                  |
| Data Quality      |  | |
| Legal Compliance  |  |  |


### 1.7.2 Output Schema





## 1.9 Use cases:
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


# 2. Requirements Matrix TODO

# 3. System Requirements TODO

# 4. Constraints TODO

## 4.1 Core Constraints TODO
- Rate limiting: Max 1 request/second per jurisdiction
- Storage: Expected 50GB/year growth **TODO Needs to be estimated. This seems like it's too large**
- Compliance: Must maintain original text alongside cleaned version.
- Availability: 99.9% uptime for API.
- Recovery: Worst-case scenario data recovery implementation.
- Data Retention: Permanent, with rapid take-down ability per legal requests.

# 5. Implementation Phases TODO


# 6. Dependencies TODO

















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