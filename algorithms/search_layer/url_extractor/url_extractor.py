# Algorithm: URL Extractor
## Purpose
Extract valid URLs from raw HTML content for legal document sources, filtering for relevant legal document repositories and government websites.

## Input
- Raw HTML content (string)
- Domain whitelist (array of strings)
- URL pattern rules (regex patterns)
- Base URL of current page (string)

## Output
- Array of validated URLs
- Metadata for each URL:
  - Source type (government, contracted repo, etc.)
  - Priority level (1-5)
  - Expected content type
  - Parent URL

## Constraints
- Memory: < 500MB per page
- Processing time: < 5s per page
- Must handle malformed HTML
- Must respect robots.txt directives

## Dependencies
- HTML Parser
- URL Validator
- Domain Classifier
- Rate Limiter

## Steps
1. Parse HTML Document
   ```python
   def parse_html(raw_html: str) -> ParsedHTML:
       try:
           return BeautifulSoup(raw_html, 'html.parser')
       except Exception as e:
           log_error("HTML parsing failed", e)
           return None
   ```

2. Extract All URLs
   ```python
   def extract_urls(parsed_html: ParsedHTML) -> List[str]:
       urls = []
       # Get href attributes from <a> tags
       urls.extend(parsed_html.find_all('a', href=True))
       # Get src attributes from <iframe> tags
       urls.extend(parsed_html.find_all('iframe', src=True))
       # Get form action URLs
       urls.extend(parsed_html.find_all('form', action=True))
       return urls
   ```

3. Normalize URLs
   ```python
   def normalize_url(url: str, base_url: str) -> str:
       # Convert relative to absolute URLs
       # Remove fragments
       # Handle URL encoding
       # Standardize protocol (https)
   ```

4. Filter URLs
   ```python
   def filter_urls(urls: List[str], whitelist: List[str]) -> List[str]:
       filtered = []
       for url in urls:
           if any(domain in url for domain in whitelist):
               if matches_legal_doc_pattern(url):
                   filtered.append(url)
       return filtered
   ```

5. Classify and Prioritize
   ```python
   def classify_url(url: str) -> URLMetadata:
       return {
           'url': url,
           'source_type': determine_source_type(url),
           'priority': calculate_priority(url),
           'expected_content': predict_content_type(url),
           'parent_url': current_page_url
       }
   ```

## Error Cases
- Malformed HTML
  - Action: Log error, attempt to extract URLs from raw text
- Invalid URLs
  - Action: Skip and log for review
- Connection timeout
  - Action: Add to retry queue
- Robot.txt violation detection
  - Action: Skip URL, adjust rate limiting

## Edge Cases
- JavaScript-generated URLs
  - Solution: Implement basic JS parsing
- Redirects
  - Solution: Follow up to 3 redirects
- PDF/Doc links without extensions
  - Solution: Check content-type headers
- Infinite loops in URL structures
  - Solution: Implement cycle detection
- International domain names
  - Solution: Implement IDNA encoding

## Validation Rules
1. URL Format:
   - Must be valid RFC 3986 format
   - Must use HTTPS protocol
   - Must resolve to valid IP

2. Domain Rules:
   - Must match whitelist patterns
   - Must be government or approved contractor
   - Must not be in blacklist

3. Path Rules:
   - Must match legal document patterns
   - Must not be admin/login pages
   - Must not be search/dynamic pages

## Performance Metrics
- URLs processed per second
- Error rate percentage
- False positive rate
- Memory usage over time
- CPU usage per page

## Testing Scenarios
1. Basic Cases
   - Standard government website
   - Common legal repository
   - Municipal code system

2. Edge Cases
   - Malformed HTML
   - JavaScript-heavy pages
   - International domains

3. Error Cases
   - Network timeout
   - Invalid HTML
   - Robot.txt violations