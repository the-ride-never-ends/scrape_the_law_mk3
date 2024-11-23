




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
Develop a system to programmatically collect, standardize, and maintain municipal legal codes from U.S. cities and counties. The system will:
- Extract legal codes from official government or government-contracted websites and databases.
- Transform raw legal text into a structured, machine-readable format
- Store processed data and metadata in a version-controlled database
- Maintain version history and track amendments
- Provide an API for accessing current and historical code versions


## 1.2 Input Specifications
| Attribute        | Specification                                        | Bounds/Constraints                      |
|------------------|------------------------------------------------------|-----------------------------------------|
| Description      | Table containing all local-level jurisdictions in US | Incorporated communities only           |
| Format           | Tabular data from a MySQL database                   | Must be convertible to UTF-8            |
| Size             | 23,089 data points                                   | Legal codes must be available online    |
| Delivery Methods | - API endpoint<br>- Terminal input<br>- File upload  | File types: SQL api, .xlsx, .csv        |
| Source Authority | 50 US states and DC                                  | Must be an approved government source   |


## 1.3 Input Processing Requirements
1. Validation
   - URL checks for availability and accessibility
   - Data integrity checks (e.g. missing values, duplicates, etc.)
   - 



2. Preprocessing
   - Non-text character removal (e.g. images, emojis, etc.)
   - Whitespace normalization
   - Encoding standardization

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