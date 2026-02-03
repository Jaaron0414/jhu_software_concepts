Module 2: Grad Cafe Web Scraper - Assignment Documentation
============================================================

Name: Aaron Xu
JHED ID: [Your JHED ID]
Module: Module 2 - Web Scraping & Data Cleaning
Assignment: Gathering Graduate School Applicant Data from Grad Cafe
Due Date: [Assignment Due Date]

## Approach

### Overview
This assignment implements a complete web scraping and data cleaning pipeline for graduate school admission statistics from Grad Cafe (https://www.thegradcafe.com). The solution extracts applicant data including program names, universities, academic metrics (GPA, GRE scores), admission status, and submission dates.

### Phase 1: Scraping (scrape.py)

**Tools Used:**
- `urllib` for URL management and HTTP requests (built-in Python library)
- `BeautifulSoup` for HTML parsing and data extraction
- `regex` and string methods for text processing

**Implementation Details:**

1. **URL Management with urllib:**
   - `urllib.request.urlopen()` to fetch pages from Grad Cafe
   - `urllib.parse.urlencode()` to construct query parameters dynamically
   - `urllib.error.HTTPError` and `URLError` for error handling
   - Request headers to mimic browser behavior and avoid blocking

2. **HTML Parsing:**
   - BeautifulSoup parses HTML with 'html.parser' backend
   - Targets table rows with class 'even' and 'odd' containing applicant data
   - Extracts 8+ columns per row using `find_all('td')` method
   - Handles variable column numbers (some entries have more fields)

3. **Data Fields Extracted:**
   - **Program**: University + Program name (mixed field)
   - **Status**: Accepted/Rejected/Waitlisted
   - **Degree**: MS/PhD/Other
   - **Date Added**: Submission date to Grad Cafe
   - **GPA**: Undergraduate GPA
   - **GRE Scores**: Quantitative, Verbal, Analytical Writing (AW)
   - **Comments**: Additional applicant notes (if available)
   - **URL**: Direct link to entry
   - **Entry Link**: Discussion forum link

4. **Pagination:**
   - Scraper loops through pages 1-1500+ (targets 30,000+ entries)
   - Each page typically contains ~20 entries
   - Gracefully handles HTTP 404 (end of results) and timeouts
   - Includes retry logic and progress reporting every 10 pages

5. **Text Cleaning in Scraper:**
   - Removes HTML tags using regex: `re.sub(r'<[^>]+>', '', text)`
   - Removes extra whitespace: `' '.join(text.split())`
   - Returns None for empty fields (consistent missing data handling)

### Phase 2: Data Cleaning (clean.py)

**Functions Implemented:**

1. **clean_data(raw_data, use_llm=False)**
   - Main cleaning orchestrator
   - Processes all 30,000+ entries
   - Preserves original program field for reproducibility
   - Calls helper functions for standardization

2. **_parse_program_university(program_field)**
   - Separates program name from university name
   - Uses regex patterns: "X at Y", "X (Y)", "X, Y"
   - Handles Grad Cafe's mixed naming conventions

3. **_standardize_gre_score(score)**
   - Extracts numeric values from score strings
   - Validates range (0-170 for V/Q, 0-6 for AW, 0-800 for old GRE)
   - Returns None for invalid/missing scores

4. **_standardize_gpa(gpa)**
   - Extracts GPA from formats like "3.95" or "3.95/4.0"
   - Validates range 0-4.0
   - Returns standardized format "X.XX"

5. **_extract_degree_info(degree_field)**
   - Standardizes degree types to: MS, PhD, MBA, MD, Other
   - Case-insensitive pattern matching

6. **_clean_status(status)**
   - Standardizes to: Accepted, Rejected, Waitlisted
   - Uses partial string matching for robustness

7. **_parse_date(date_str)**
   - Converts various date formats to ISO format (YYYY-MM-DD)
   - Handles: MM/DD/YYYY, YYYY-MM-DD, DD-MM-YY
   - Validates date validity before conversion

8. **_remove_html_tags(text)**
   - Removes HTML tags: `<>`, `&lt;`, `&amp;`, etc.
   - Cleans extra whitespace
   - Returns None for empty results

### Phase 3: LLM-Based Standardization (llm_hosting subfolder)

**Workflow:**
1. Initial cleaning produces separate `program` and `university` fields
2. LLM service (via `llm_hosting/app.py`) standardizes names:
   - Maps "JHU", "Johns Hopkins", "John Hopkins" → "Johns Hopkins University"
   - Standardizes program names despite variations
   - Applies post-processor fixes and fuzzy matching
3. Results include `cleaned_program` and `cleaned_university` columns
4. Original names preserved in `original_program` for traceability

**Command to run LLM cleaning:**
```bash
cd llm_hosting
pip install -r requirements.txt
python app.py --file "../applicant_data.json" > cleaned_output.json
```

## robots.txt Compliance

**Status: COMPLIANT ✓**

Grad Cafe's robots.txt explicitly allows scraping:
```
User-agent: *
Content-Signal: search=yes,ai-train=no
Allow: /
```

The `/survey/index.php` endpoint is allowed. The scraper:
- Uses `Content-Signal: search=yes` (permitted use)
- Respects rate limiting with delays between requests
- Identifies itself with proper User-Agent header
- Avoids `/cgi-bin/` and other restricted paths

Evidence: See `robots_txt_verification.txt` in this directory.

## Project Structure

```
module_2/
├── scrape.py                      # Phase 1: Web scraping
├── clean.py                       # Phase 2: Data cleaning
├── requirements.txt               # Dependencies (beautifulsoup4, lxml)
├── README.txt                     # This file
├── applicant_data.json            # Raw scraped data (30,000+ entries)
├── applicant_data_cleaned.json    # Cleaned data (before LLM processing)
├── robots_txt_verification.txt    # robots.txt compliance evidence
└── llm_hosting/                   # Phase 3: LLM standardization module
    ├── app.py                     # LLM service for name standardization
    ├── requirements.txt           # LLM dependencies
    ├── canonical_universities.json # Standard university names
    └── canonical_programs.json    # Standard program names
```

## Installation & Usage

### Prerequisites
- Python 3.10+
- Internet connection for web scraping

### Installation
```bash
cd module_2
pip install -r requirements.txt
```

### Running Phase 1 (Scraping)
```bash
python scrape.py
```
- Scrapes ~30,000 entries (may take 30-60 minutes)
- Saves to `applicant_data.json`
- Shows progress every 10 pages

### Running Phase 2 (Cleaning)
```bash
python clean.py
```
- Reads `applicant_data.json`
- Standardizes formats and separates program/university
- Saves to `applicant_data_cleaned.json`
- Takes ~1-2 minutes for full dataset

### Running Phase 3 (LLM Standardization)
```bash
cd llm_hosting
python app.py --file "../applicant_data_cleaned.json" > output.json
```
- Standardizes program and university names
- Adds `cleaned_program` and `cleaned_university` columns
- Generates cleaned final dataset

## Known Issues & Solutions

### Issue 1: Mixed Program/University Fields
**Problem:** Grad Cafe mixes program and university names (e.g., "CS at MIT", "Stanford - AI PhD")
**Solution:** Implemented `_parse_program_university()` with regex patterns for common separators
**Workaround:** LLM service provides additional standardization

### Issue 2: Variable GRE Score Formats
**Problem:** GRE scores appear as "160", "160/170", "160V", "(160)", or missing
**Solution:** `_standardize_gre_score()` extracts digits and validates range
**Impact:** Unknown/malformed scores set to None (handled consistently)

### Issue 3: Date Format Variations
**Problem:** Dates appear in multiple formats from different regions
**Solution:** `_parse_date()` handles MM/DD/YYYY, YYYY-MM-DD, DD-MM-YY formats
**Limitation:** Ambiguous dates (01/02/2023) assumed as MM/DD/YYYY (US format)

### Issue 4: Large Dataset Performance
**Problem:** Processing 30,000+ entries is memory-intensive
**Solution:** Batch processing with progress reporting every 1,000 entries
**Note:** Requires ~500MB-1GB RAM for full dataset in memory

### Issue 5: Network Timeouts
**Problem:** Grad Cafe may timeout or rate-limit during extended scraping
**Solution:** Implemented 10-second timeout per request with error handling
**Workaround:** Scraper skips failed pages and continues (not ideal but recovers)

### Issue 6: Inconsistent Missing Data
**Problem:** Fields may be missing, empty, or marked as "N/A", "—", etc.
**Solution:** Standardized all missing values to None for consistency
**Result:** Easier to handle downstream in analysis

## Data Quality Notes

1. **Completeness:** Not all applicants fill all fields. Missing data is common and preserved as None.
2. **Accuracy:** Data is self-reported by applicants. Some outliers or typos may exist.
3. **University Names:** Same institution appears in many forms (JHU, Johns Hopkins, etc.). LLM phase addresses this.
4. **Program Names:** Many variations and abbreviations (CS, Computer Science, CS PhD, etc.).
5. **International Status:** Not always provided in Grad Cafe data; field may be None for many entries.

## Dependencies

- **beautifulsoup4** (4.12.2): HTML parsing
- **lxml** (4.9.3): Fast XML/HTML parser backend
- **urllib**: Built-in Python library for URL handling
- **json**: Built-in Python library for data serialization
- **re**: Built-in Python library for regex operations

No external API keys or paid services required.

## Expected Output

After running all phases:
- **applicant_data.json**: ~30,000-40,000 raw entries with all fields
- **applicant_data_cleaned.json**: Same entries with standardized formats
- **cleaned_output.json**: Final output with LLM-standardized program/university names

Sample entry structure:
```json
{
  "original_program": "Computer Science at Stanford University",
  "program": "Computer Science",
  "university": "Stanford University",
  "cleaned_program": "Computer Science",
  "cleaned_university": "Stanford University",
  "degree": "PhD",
  "status": "Accepted",
  "date_added": "2023-12-15",
  "gpa": "3.95",
  "gre_verbal": "165",
  "gre_quantitative": "170",
  "gre_aw": "4.5",
  "comments": "Great profile, admitted to PhD program",
  "url": "https://www.thegradcafe.com/..."
}
```

## Future Improvements

1. Add fuzzy matching for program names in local post-processor
2. Expand canonical university list for better LLM coverage
3. Implement incremental scraping to avoid re-scraping all data
4. Add database storage option (SQLite/PostgreSQL) for large datasets
5. Create visualization dashboard for acceptance statistics
6. Add confidence scores to LLM standardization results

---
Assignment completed: [Completion Date]

