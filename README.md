# Program: scrape_the_law_mk3
# Authors: Kyle Rose, Claude 3.5 Sonnet


## Overview
3rd version of scrape_the_law, per Endo's comments and critiques.
scrape_the_law_mk3 is a web scraping system to collect municipal legal codes from all 22,899 US cities and counties and store them in a structured SQL database.

## Key Features
- Extract legal documents from official government or government-contracted websites and databases.
- Parse and standardize raw content into tabular data with metadata
- Store in SQL database with proper relationships and versioning
- Maintain version history and track code updates/amendments
- Handle different website structures and content formats

## Dependencies
- pyyaml
- aiohttp
- pytest-playwright
- pandas
- aiomysql
- beautifulsoup4
- requests
- multipledispatch
- pymysql
- selenium
- mysql-connector-python

## Usage
```bat
call install.bat
call start.bat
```
