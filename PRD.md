# Program: scrape_the_law_mk3
**Version: 0.1.1**<br>
**Authors: Kyle Rose, Claude 3.5 Sonnet, Codestral**

# Table of Contents

1. Problem Definition
   1.1 Problem Statement
   1.2 Objective
   1.3 Global Success Metrics
   1.4 Success Metrics by Stakeholder Type
   1.5 Seed Dataset Specifications
   1.6 Legal Document Source Specifications
   1.7 Input Processing Requirements
   1.8 Inputs
      1.8.1 Input Type Specifications
      1.8.2 Input Processing Requirements
   1.9 Output
      1.9.1 Output Specifications
      1.9.2 Output Schema
   1.10 Risk Assessment

2. Success Criteria
   2.1 Minimum Viable Product (MVP)
   2.2 MVP Timeline

3. Scope Definition
   3.1 In Scope
   3.2 Explicitly Out of Scope

4. Primary Use Cases
5. System Requirements
   5.1 Performance Requirements
   5.2 Hardware Requirements
6. Constraints
   6.1 Business Constraints
   6.2 Technical Constraints
7. Implementation Phases
8. Dependencies
   8.1 Software Dependencies
   8.2 Third-Party Services

9. Requirements Matrix: MVP


## NOTE: Termonology Shorthand
For the sake of brevity, the following shorthand will be used where it does not fundamentally change the intent or meaning of the text.
| Termonology                        | Shorthand                  |
|------------------------------------|----------------------------|
| 'incorporated places and counties' | 'cities'.                  |
| 'legal text', 'legal document'     | 'law'/'laws'               |
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
- Extract laws from official government or government-contracted websites and databases.
- Parse and standardize raw content into tabular data with metadata
- Store in a database with proper relationships and versioning
- Maintain version history and track code updates/amendments
- Handle different website structures and content formats


### 1.3 Global Success Metrics
| Category     | Metric                        | Minimum Target  | Optimal Target  | Measurement Method                                           |
|--------------|-------------------------------|-----------------|-----------------|--------------------------------------------------------------|
| Coverage     | % of US cities covered        | 50%             | 95%             | Codes available / Total # cities                             |
| Accuracy     | Text accuracy vs. source      | 99%             | 99.99%          | Error rate per 1000 words                                    |
| Completeness | Code section coverage         | 95%             | 99.99%          | Code Sections Available / Total # Code Sections              |
| Transparency | Source attribution available  | 100%            | 100%            | Content with Metadata / Total Content                        |
| Freshness    | Update lag time               | < 30 days       | < 7 days        | Update timestamp vs rate of change of versions               |
| Availability | System uptime                 | 99%             | 99.99%          | Time available over a rolling 30-day period                  |
| Performance  | Average query response time   | < 2s            | < 200ms         | API response timing                                          |
| Consistency  | Format standardization        | 95%             | 99.99%          | Random sample of content chunks vs pre-defined standard      |
| Scalability  | Data growth handling          | +200GB per year | +500GB per year | System performance monitoring                                |
| Reliability  | Error rate in data processing | < 1%            | < 0.1%          | Error rate per 1000 content chunks                           |

## 1.4 Success Metrics by Stakeholder Type

### 1.4.1 Legal/Government Stakeholders
| Stakeholder | Primary Needs | Metric | Target | Measurement Method |
|-------------|--------------|---------|---------|-------------------|
| Lawyers | - Fast access to relevant codes<br>- Accuracy of legal text<br>- Version history | - Search response time<br>- Text accuracy rate<br>- Version tracking completeness | - < 2s search time<br>- 99.9% accuracy<br>- 100% version coverage | - API response timing<br>- Random sample audit<br>- Version history validation |
| Lawmakers | - Cross-jurisdiction comparisons<br>- Amendment tracking<br>- Code relationships | - Cross-reference completeness<br>- Amendment detection rate<br>- Relationship mapping accuracy | - 95% reference coverage<br>- 98% amendment detection<br>- 90% relationship accuracy | - Coverage analysis<br>- Change detection audit<br>- Graph validation |
| Government Agencies | - Cross-agency coordination<br>- Policy impact analysis<br>- Regulatory compliance | - Inter-agency reference tracking<br>- Policy change impacts<br>- Compliance overlap detection | - 95% agency coverage<br>- < 48hr impact analysis<br>- 98% overlap detection | - Agency validation<br>- Change impact tracking<br>- Overlap analysis tools |
| City Planners | - Zoning regulations<br>- Development guidelines<br>- Environmental regulations | - Spatial data integration<br>- Code visualization accuracy<br>- Environmental compliance tracking | - 90% spatial integration<br>- 95% visualization accuracy<br>- 100% env. tracking | - GIS validation<br>- Visual audit<br>- Compliance checks |


### 1.4.2 Business/Industry Stakeholders
| Stakeholder | Primary Needs | Metric | Target | Measurement Method |
|-------------|--------------|---------|---------|-------------------|
| Business Owners | - Compliance guidance<br>- Plain language summaries<br>- Jurisdiction coverage | - Jurisdictional coverage<br>- Update timeliness<br>- Code accessibility | - 80% jurisdiction coverage<br>- < 30 day update lag<br>- > 95% availability | - Coverage tracking<br>- Update monitoring<br>- Uptime monitoring |
| Real Estate Developers | - Land use regulations<br>- Building codes<br>- Permit requirements | - Regulation completeness<br>- Code update tracking<br>- Permit requirement accuracy | - 98% coverage<br>- < 24hr updates<br>- 100% requirement accuracy | - Coverage audit<br>- Update monitoring<br>- Requirement validation |
| Insurance Companies | - Risk assessment<br>- Compliance verification<br>- Jurisdiction comparison | - Risk factor extraction<br>- Compliance tracking<br>- Cross-jurisdiction analysis | - 95% risk coverage<br>- 100% compliance tracking<br>- 90% comparison accuracy | - Risk validation<br>- Compliance audit<br>- Analysis verification |
| Small Business Associations | - Simplified compliance guides<br>- Cost impact analysis<br>- Local variation tracking | - Guide clarity<br>- Cost assessment accuracy<br>- Variation detection | - 90% clarity rating<br>- 95% cost accuracy<br>- 98% variation detection | - User feedback<br>- Cost validation<br>- Variation audit |


### 1.4.3 Research/Academic Stakeholders
| Stakeholder | Primary Needs | Metric | Target | Measurement Method |
|-------------|--------------|---------|---------|-------------------|
| Legal Scholars | - Historical analysis<br>- Pattern identification<br>- Complete metadata | - Historical depth<br>- Metadata completeness<br>- Citation accuracy | - 10 year history<br>- 98% metadata coverage<br>- 99% citation accuracy | - Historical audit<br>- Metadata validation<br>- Citation checking |
| Social Science Researchers | - Data standardization<br>- API accessibility<br>- Bulk downloads | - Data format consistency<br>- API uptime<br>- Download completeness | - 100% standardization<br>- 99.9% API uptime<br>- 100% download success | - Format validation<br>- Uptime monitoring<br>- Download verification |
| Academic Institutions | - Research datasets<br>- Teaching materials<br>- Citation standards | - Dataset completeness<br>- Educational usefulness<br>- Citation accuracy | - 99% completeness<br>- 90% usefulness rating<br>- 100% citation accuracy | - Dataset validation<br>- User surveys<br>- Citation checks |


### 1.4.4 Public Interest/Advocacy Stakeholders
| Stakeholder | Primary Needs | Metric | Target | Measurement Method |
|-------------|---------------|--------|--------|--------------------|
| Anti-corruption Activists | - Transparency metrics<br>- Change tracking<br>- Public accessibility | - Change detection rate<br>- Public access rate<br>- Update transparency | - 100% change tracking<br>- 100% public access<br>- < 24hr update notice | - Change log audit<br>- Access monitoring<br>- Update timing tracking |
| Civil Rights Organizations | - Discrimination detection<br>- Accessibility compliance<br>- Equal protection analysis | - Bias detection rate<br>- ADA compliance<br>- Protection coverage | - 95% detection rate<br>- 100% ADA compliance<br>- 100% coverage | - Bias analysis<br>- Compliance check<br>- Coverage audit |
| Environmental Groups | - Environmental regulations<br>- Impact assessments<br>- Compliance tracking | - Environmental code coverage<br>- Assessment completeness<br>- Violation tracking | - 100% env. coverage<br>- 95% assessment coverage<br>- 100% violation tracking | - Coverage analysis<br>- Assessment audit<br>- Violation monitoring |
| Journalists | - Quick fact verification<br>- Historical context<br>- Source attribution | - Search accuracy<br>- Historical coverage<br>- Citation completeness | - 99% search precision<br>- 10 year history<br>- 100% attribution | - Search testing<br>- Timeline validation<br>- Citation audit |


### 1.4.5 Technical Stakeholders
| Stakeholder | Primary Needs | Metric | Target | Measurement Method |
|-------------|--------------|---------|---------|-------------------|
| Software Developers | - API stability<br>- Documentation quality<br>- Data format consistency | - API versioning<br>- Doc completeness<br>- Schema validation | - 99.9% API stability<br>- 100% doc coverage<br>- 100% schema compliance | - Version monitoring<br>- Doc coverage audit<br>- Schema validation |
| AI Researchers | - Clean training data<br>- Consistent formatting<br>- Ground truth annotations | - Data cleaning quality<br>- Format standardization<br>- Annotation accuracy | - 99.9% data cleanliness<br>- 100% format compliance<br>- 98% annotation accuracy | - Data quality audit<br>- Format validation<br>- Annotation verification |


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




### 1.5 Success Criteria
### 1.5.1 Minimum Viable Product (MVP)
| Feature                        | Description                          | Minimum Success Criteria | Optimal Success Criteria |
|--------------------------------|--------------------------------------|--------------------------|--------------------------|
| Scraping Functionality         | Fully scrape 1 law repo              |  Download all raw versions legal docs for each city on the repo |- Download all repos | <br>- Completes in < 1 week<br> |
| Docs Type Support              | Extraction, cleaning, and validation of law docs | -  Support extraction, validation, and cleaning for HTML, text PDFs <br>- Flags non-textual docs like graphs, tables, and images |
| Persistant Docs Storage        | Database of raw and cleaned Docs | - Efficiently stores plain-text copies of HTML and PDF Docs <br>- Handles UTF-8 encoding |
| Docs Extraction Rate           | # of docs scraped per hour | 5 docs per hour. | 100 docs per hour. |
| Docs Conversion Error Rate     | Errors in Docs extraction, cleaning, and validation. |- Minimum: 90% <br> - Optimal: 100%
| Error Handling                 | Input extraction, validation and error reporting | - Catches and reports common errors <br>- Provides clear error messages |
| Legal Compliance               | Alert user to legal notices from stakeholders | - Logs and alerts user to legal notices <br> - Automated take-down measures <br> |


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
### 1.6.1 In Scope
| Feature                      | Description                                                                                      |
|------------------------------|--------------------------------------------------------------------------------------------------|
| Data Collection              | - Web scraping from verified sources<br>- Periodic updates (e.g., monthly)<br>- Version tracking |
| Data Processing              | - Text extraction from various formats (HTML, PDF, etc.)<br>- Basic data cleaning and formatting |
| Data Storage                 | - Structured database for legal codes<br>- Metadata storage (source, date, etc.)                 |
| Basic Search                 | - Keyword and jurisdiction-based search functionality                                            |
| API Access                   | - Read-only access to stored data<br>- Basic query parameters                                    |
| Error Handling               | - Basic error logging and reporting                                                              |
| Legal Compliance             | - Source attribution<br>- Compliance with terms of service for source websites                   |

### 1.6.2 Explicitly Out of Scope
| Feature                      | Description                                                                                                  |
|------------------------------|--------------------------------------------------------------------------------------------------------------|
| Real-time Gathering          | - Live document updates<br>- Websocket connections<br>- Real-time collaboration                              |
| Advanced Features            | - Data extraction beyond basic text<br>- Automated legal analysis<br>- Custom template creation              |
| Integration Features         | - CI/CD pipeline integration<br>- IDE plugins<br>- Direct repository management                              |
| Authentication/Authorization | - User management<br>- Role-based access<br>- Multi-tenant support                                           |
| Advanced Search              | - Natural language processing<br>- Semantic search capabilities                                              |
| Data Interpretation          | - Legal analysis or interpretation of collected data                                                         |
| User Interface               | - Graphical user interface for data exploration (beyond basic API)                                           |




## 1.10 Risk Assessment
### 1.10.1 Technical Risks
| Risk                    | Probability | Impact | Mitigation Strategy              |
|-------------------------|-------------|--------|----------------------------------|
| Data corruption         | Low         | High   | Regular backups, checksums       |
| System downtime         | Medium      | High   | Redundancy, monitoring           |
| Performance degradation | Medium      | Medium | Load testing, optimization       |
| Database scalability    | Low         | High   | Sharding, indexing               |
| API failures            | Medium      | Medium | Circuit breakers, fallbacks      |

### 1.10.2 Legal Risks
| Risk                        | Probability | Impact | Mitigation Strategy                   |
|-----------------------------|-------------|--------|---------------------------------------|
| Copyright violation         | Medium      | High   | Terms monitoring, takedown process    |
| Data privacy breach         | Low         | High   | Encryption, access controls           |
| Terms of service violation  | Medium      | Medium | Rate limiting, compliance checks      |
| Regulatory non-compliance   | Low         | High   | Legal review, documentation           |
| License violations          | Low         | Medium | License audit, compliance tracking    |

### 1.10.3 Resource Risks
| Risk               | Probability | Impact | Mitigation Strategy                |
|--------------------|-------------|--------|------------------------------------|
| Storage capacity   | Medium      | Medium | Monitoring, cleanup jobs           |
| Processing power   | High        | Medium | Auto-scaling, optimization         |
| Network bandwidth  | Medium      | High   | CDN, caching                       |
| Cost overrun       | High        | High   | Budget monitoring, optimization    |
| Service quotas     | Low         | Medium | Quota monitoring, fallbacks        |




# 2. Requirements Matrix: MVP

| Requirement ID | Description | Priority | Complexity | Status | Associated MVP Feature |
|----------------|-------------|----------|------------|--------|------------------------|
| REQ-001 | System shall fully scrape 1 law repository | High | High | Started | Scraping Functionality |
| REQ-002 | System shall support extraction from HTML and text PDF formats | High | Medium | Started | Docs Type Support |
| REQ-003 | System shall store raw and cleaned versions of laws | High | Medium | Started | Persistant Docs Storage |
| REQ-004 | System shall extract at least 5 docs per hour | High | Medium | Not Started | Docs Extraction Rate |
| REQ-005 | System shall have less than 10% error rate in doc conversion | High | Medium | Not Started | Docs Conversion Error Rate |
| REQ-006 | System shall catch and report common errors | Medium | Medium | Started | Error Handling |
| REQ-007 | System shall log and alert user to legal notices | High | Low | Not Started | Legal Compliance |
| REQ-008 | System shall flag non-textual content like graphs, tables, and images | Medium | Medium | Not Started | Docs Type Support |
| REQ-009 | System shall efficiently store plain-text copies of HTML and PDF docs | High | Medium | Started | Persistant Docs Storage |
| REQ-010 | System shall handle UTF-8 encoding | Medium | Low | Started | Persistant Docs Storage |
| REQ-011 | System shall provide clear error messages | Medium | Low | Started | Error Handling |
| REQ-012 | System shall have automated take-down measures | High | Medium | Not Started | Legal Compliance |


# 4. Constraints

## 4.1 Business Constraints
### 4.1.1 Budget Limits
- Initial development budget: $0
- Monthly operational budget: $0
- Cloud services budget: None (open-source solutions preferred)
- Contingency fund: None

### 4.1.2 Timeline Restrictions
- Project kickoff: December 1, 2024
- MVP delivery: December 31st, 2024 (1 month)
- Full system launch: June 30, 2025 (6 months)
- Quarterly review and update cycles

### 4.1.3 Resource Availability
- Development team: 1 part-time developer i.e. me
- Infrastructure: Limited to developer's computer.
- Legal counsel: NA
- Data storage: Initial capacity of 500GB, scalable to 5TB

### 4.1.4 Regulatory Requirements
- GDPR compliance for handling any EU-related data
- CCPA compliance for California residents' data
- SOC 2 Type II certification within 12 months of launch
- Adherence to Open Data principles as defined by the Open Knowledge Foundation

### 4.1.5 Stakeholder Expectations
- Monthly progress reports to project sponsors
- Bi-weekly demos to key stakeholders
- User acceptance testing with a panel of 10 legal professionals

### 4.1.6 Scalability Constraints
- System must support up to 10 unique monthly users
- Database must efficiently handle up to 10 million docs
- Database must efficiently handle expected 50GB/year growth 
- API must support up to 1,000 requests per minute

### 4.1.7 Maintenance and Support
- 99.9% uptime guarantee during business hours (9am-5pm EST)
- 24/7 automated monitoring with alerts
- Maximum 4-hour response time for critical issues
- Implementations for worst-case scenario data recovery must be in place.

### 4.1.8 Licensing and Partnerships
- All third-party libraries must have compatible open-source licenses
- No exclusive partnerships that limit data accessibility



# 5. Implementation Phases TODO






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