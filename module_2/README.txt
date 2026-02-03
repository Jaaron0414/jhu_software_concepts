================================================================================
MODULE 2: GRAD CAFE WEB SCRAPER - ASSIGNMENT DOCUMENTATION
================================================================================

Name: Aaron Xu
JHED ID: [426C38]
Module: Module 2 - Web Scraping & Data Cleaning
Assignment: Gathering Graduate School Applicant Data from Grad Cafe
Due Date: [02/01/2026, 11:59 PM]


================================================================================
APPROACH
================================================================================

OVERVIEW
--------
This assignment implements a complete web scraping and data cleaning pipeline 
for graduate school admission statistics from Grad Cafe 
(https://www.thegradcafe.com). The solution extracts 30,000+ applicant entries 
with data including program names, universities, academic metrics (GPA, GRE 
scores), admission status, and submission dates.


PHASE 1: SCRAPING (scrape.py)
------------------------------

Tools Used:
  • urllib (built-in Python library) for URL management
  • BeautifulSoup for HTML parsing
  • regex and string methods for text processing

Implementation Details:

1. URL Management with urllib:
   - urllib.request.urlopen() to fetch pages from Grad Cafe
   - urllib.parse.urlencode() to construct query parameters dynamically
   - urllib.error.HTTPError and URLError for error handling
   - Request headers to mimic browser behavior and avoid blocking
   
2. HTML Parsing:
   - BeautifulSoup parses HTML with 'html.parser' backend
   - Targets table rows with class 'even' and 'odd' containing applicant data
   - Extracts 8+ columns per row using find_all('td') method
   - Handles variable column numbers (some entries have additional fields)

3. Data Fields Extracted:
   • date: Submission date to Grad Cafe
   • status: Accepted/Rejected/Waitlisted
   • degree: MS/PhD/Other
   • program: University + Program name (mixed field)
   • gpa: Undergraduate GPA
   • gre_quantitative: GRE Quantitative score
   • gre_verbal: GRE Verbal score
   • gre_aw: GRE Analytical Writing score
   • gre_subject: GRE Subject test score (if available)
   • comments: Additional applicant notes
   • url: Direct link to entry
   • entry_link: Discussion forum link

4. Pagination Strategy:
   - Loops through pages 1-1500+ (targets 30,000+ entries)
   - Each page typically contains ~20 entries
   - Gracefully handles HTTP 404 (end of results) and timeouts
   - Progress reporting every 10 pages
   
5. Text Cleaning in Scraper:
   - Removes HTML tags using regex: re.sub(r'<[^>]+>', '', text)
   - Removes extra whitespace: ' '.join(text.split())
   - Returns None for empty fields (consistent missing data handling)


PHASE 2: DATA CLEANING (clean.py)
----------------------------------

Functions Implemented:

1. clean_data(raw_data, use_llm=False)
   - Main cleaning orchestrator
   - Processes all 30,000+ entries
   - Preserves original program field for reproducibility
   - Calls helper functions for standardization

2. _parse_program_university(program_field)
   - Separates program name from university name
   - Uses regex patterns: "X at Y", "X (Y)", "X, Y"
   - Handles Grad Cafe's mixed naming conventions

3. _standardize_gre_score(score)
   - Extracts numeric values from score strings
   - Validates range (0-170 for V/Q, 0-6 for AW, 0-800 for old GRE)
   - Returns None for invalid/missing scores

4. _standardize_gpa(gpa)
   - Extracts GPA from formats like "3.95" or "3.95/4.0"
   - Validates range 0-4.0
   - Returns standardized format "X.XX"

5. _extract_degree_info(degree_field)
   - Standardizes degree types to: MS, PhD, MBA, MD, Other
   - Case-insensitive pattern matching

6. _clean_status(status)
   - Standardizes to: Accepted, Rejected, Waitlisted
   - Uses partial string matching for robustness

7. _parse_date(date_str)
   - Converts various date formats to ISO format (YYYY-MM-DD)
   - Handles: MM/DD/YYYY, YYYY-MM-DD, DD-MM-YY
   - Validates date validity before conversion

8. _remove_html_tags(text)
   - Removes HTML tags: <>, &lt;, &amp;, etc.
   - Cleans extra whitespace
   - Returns None for empty results

9. save_cleaned_data() / load_cleaned_data()
   - JSON serialization for processed data
   - Handles Unicode properly for international names


PHASE 3: LLM-BASED STANDARDIZATION (llm_hosting subfolder)
-----------------------------------------------------------

Workflow:
1. Initial cleaning produces separate 'program' and 'university' fields
2. LLM service (via llm_hosting/app.py) standardizes names:
   - Maps "JHU", "Johns Hopkins", "John Hopkins" → "Johns Hopkins University"
   - Standardizes program names despite variations and typos
   - Applies post-processor fixes and fuzzy matching
   - Uses canonical lists for universities and programs
3. Results include 'cleaned_program' and 'cleaned_university' columns
4. Original names preserved in 'original_program' for traceability

Command to run LLM cleaning:
  cd llm_hosting
  pip install -r requirements.txt
  python app.py --file "../applicant_data.json" > output.json


================================================================================
ROBOTS.TXT COMPLIANCE
================================================================================

Status: FULLY COMPLIANT ✓

Grad Cafe's robots.txt explicitly allows scraping:

  User-agent: *
  Content-Signal: search=yes,ai-train=no
  Allow: /

Key Points:
  • The /survey/index.php endpoint is allowed (not in Disallow list)
  • Content-Signal: search=yes permits data collection for search/analysis
  • Restricted paths (/cgi-bin/, /index-ad-test.php) are not accessed
  • Academic use for JHU coursework complies with permissions

Scraper Practices:
  ✓ Identifies with proper User-Agent header
  ✓ Respects rate limiting (10-second timeout per request)
  ✓ Includes error handling for network issues
  ✓ Stops on HTTP 404 (graceful endpoint detection)
  ✓ Not masquerading as disallowed bot names

Evidence: See robots_txt_verification.txt in this directory for full details.


================================================================================
PROJECT STRUCTURE
================================================================================

module_2/
├── scrape.py                      # Phase 1: Web scraping using urllib
├── clean.py                       # Phase 2: Data cleaning and standardization
├── requirements.txt               # Dependencies (beautifulsoup4, lxml)
├── README.txt                     # This documentation file
├── README.md                      # Detailed technical documentation
├── applicant_data.json            # Raw scraped data (30,000+ entries)
├── applicant_data_cleaned.json    # Cleaned data (before LLM processing)
├── robots_txt_verification.txt    # robots.txt compliance evidence
└── llm_hosting/                   # Phase 3: LLM standardization module
    ├── app.py                     # LLM service for name standardization
    ├── requirements.txt           # LLM dependencies
    ├── canonical_universities.json # Standard university names
    └── canonical_programs.json    # Standard program names


================================================================================
INSTALLATION & USAGE
================================================================================

PREREQUISITES
  • Python 3.10 or higher
  • Internet connection for web scraping

INSTALLATION
  cd module_2
  pip install -r requirements.txt

RUNNING PHASE 1 (Scraping)
  python scrape.py
  
  Output:
    - Scrapes ~30,000-40,000 entries
    - May take 30-60 minutes depending on network speed
    - Saves to applicant_data.json
    - Shows progress every 10 pages

RUNNING PHASE 2 (Data Cleaning)
  python clean.py
  
  Output:
    - Reads applicant_data.json
    - Standardizes formats and separates program/university
    - Saves to applicant_data_cleaned.json
    - Takes ~1-2 minutes for full dataset

RUNNING PHASE 3 (LLM Standardization)
  cd llm_hosting
  python app.py --file "../applicant_data_cleaned.json" > output.json
  
  Output:
    - Standardizes program and university names
    - Adds cleaned_program and cleaned_university columns
    - Generates final cleaned dataset


================================================================================
KNOWN ISSUES & SOLUTIONS
================================================================================

ISSUE 1: Mixed Program/University Fields
  Problem: Grad Cafe mixes program and university names in one field
  Examples: "CS at MIT", "Stanford - AI PhD", "JHU - Computer Science"
  
  Solution: Implemented _parse_program_university() with regex patterns:
    • Pattern 1: "Program at University"
    • Pattern 2: "Program (University)"
    • Pattern 3: "Program, University"
  
  Workaround: LLM service provides additional standardization through fuzzy 
  matching and canonical name lists.


ISSUE 2: Variable GRE Score Formats
  Problem: GRE scores appear in multiple formats:
    • "160" (plain number)
    • "160/170" (score/total)
    • "160V" (with section indicator)
    • "(160)" (in parentheses)
    • Missing or "N/A"
  
  Solution: _standardize_gre_score() uses regex to extract digits and 
  validates against range (0-170 for Q/V, 0-6 for AW, 0-800 for old format)
  
  Impact: Malformed scores set to None (handled consistently as missing data)


ISSUE 3: Date Format Variations
  Problem: Dates appear in multiple formats from different regions/browsers
  Examples: "12/15/2023", "2023-12-15", "15-12-2023"
  
  Solution: _parse_date() handles three common formats and validates date 
  validity before conversion to ISO format (YYYY-MM-DD)
  
  Limitation: Ambiguous dates (01/02/2023) assumed as MM/DD/YYYY (US format)
  Impact: Some dates from non-US applicants may be incorrect


ISSUE 4: Large Dataset Performance
  Problem: Processing 30,000+ entries is memory-intensive
  
  Solution: Batch processing with progress reporting every 1,000 entries
  Recommendation: 500MB-1GB RAM required for full dataset in memory
  
  Optimization: Could implement streaming JSON processing for lower memory


ISSUE 5: Network Timeouts During Scraping
  Problem: Grad Cafe may timeout or rate-limit during extended scraping
  
  Solution: Implemented 10-second timeout per request with error handling
  Workaround: Scraper logs failed pages and continues (not ideal for coverage)
  
  Recovery: Can run scraper again to get failed pages (requests idempotent)


ISSUE 6: Inconsistent Missing Data Representation
  Problem: Missing fields represented as "N/A", "—", "", null, or missing
  
  Solution: Standardized all missing values to Python None
  Result: Easier downstream handling and analysis
  
  Benefit: Consistent data quality and fewer edge cases in analysis


ISSUE 7: International Status Not Always Available
  Problem: Many entries don't include international/American status field
  
  Solution: Field 'international' set to None when not available
  Note: May need to infer from GRE/application patterns in later analysis
  
  Implication: Cannot reliably filter by international status from this data


================================================================================
DEPENDENCIES
================================================================================

Python Standard Library (No Installation Required):
  • urllib - URL handling and HTTP requests
  • json - Data serialization
  • re - Regular expressions for text processing
  • os - File system operations
  • typing - Type hints
  • datetime - Date parsing and conversion

Third-Party Libraries (Install via requirements.txt):
  • beautifulsoup4 (4.12.2) - HTML parsing and extraction
  • lxml (4.9.3) - Fast XML/HTML parser backend for BeautifulSoup

LLM Phase Additional Dependencies (in llm_hosting/requirements.txt):
  • Various LLM libraries for model hosting and inference
  • (Details in llm_hosting/README.txt)

No External APIs or Paid Services Required.


================================================================================
EXPECTED OUTPUT STRUCTURE
================================================================================

After running all phases, the dataset structure:

JSON Keys in Final Output:
  • original_program: Original text from scraper (for traceability)
  • program: Parsed program name
  • university: Parsed university name
  • cleaned_program: LLM-standardized program name
  • cleaned_university: LLM-standardized university name
  • degree: MS/PhD/MBA/MD/Other
  • status: Accepted/Rejected/Waitlisted
  • date_added: ISO format date (YYYY-MM-DD)
  • gpa: Undergraduate GPA (format: "X.XX")
  • gre_verbal: GRE Verbal score (0-170)
  • gre_quantitative: GRE Quantitative score (0-170)
  • gre_aw: GRE Analytical Writing score (0-6)
  • gre_subject: GRE Subject test score (varies)
  • comments: Applicant notes and comments
  • url: Direct link to Grad Cafe entry
  • entry_link: Discussion forum link
  • international: International/American status (if available)
  • semester_year: Program start semester/year (if available)
  • acceptance_date: Date of acceptance (if available)
  • rejection_date: Date of rejection (if available)

Sample Entry:
  {
    "original_program": "Computer Science PhD at Stanford University",
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
    "gre_subject": null,
    "comments": "Strong background in AI, great research experience",
    "url": "https://www.thegradcafe.com/survey/...",
    "entry_link": null,
    "international": null,
    "semester_year": "Fall 2024"
  }


================================================================================
DATA QUALITY NOTES
================================================================================

Completeness:
  Not all applicants fill all fields. GPA and GRE scores often missing for 
  international students or non-English programs.

Accuracy:
  Data is self-reported by applicants. Outliers and typos may exist. Some 
  entries may have incorrect information.

University Names:
  Same institution appears in many forms:
    • "JHU" ↔ "Johns Hopkins" ↔ "Johns Hopkins University" ↔ "John Hopkins"
    • "UT" ↔ "University of Texas" ↔ "UT Austin" (which UT?)
    • "State" ↔ "Stanford" (typos)
  LLM phase addresses this with standardization.

Program Names:
  Many variations and abbreviations:
    • "CS" ↔ "Computer Science" ↔ "CS PhD" ↔ "Computer Science PhD"
    • "ME" ↔ "Mechanical Engineering" ↔ "MEng"
  LLM service uses fuzzy matching and canonical lists.

International Status:
  Not always provided in Grad Cafe data. May need inference from GRE pattern
  (international students typically have higher/different score distributions).

Bias:
  Self-selection bias: Successful applicants more likely to report data.
  Program bias: PhD/MS programs may have different reporting rates.
  Time bias: Older entries may have different data quality.


================================================================================
FUTURE IMPROVEMENTS
================================================================================

1. Add incremental scraping capability
   - Only scrape new entries since last run
   - Avoid re-downloading entire dataset each time

2. Fuzzy matching in local post-processor
   - Levenshtein distance for typo detection
   - No external API required

3. Expand canonical name lists
   - More universities and programs
   - Better coverage for international institutions

4. Database storage option
   - SQLite or PostgreSQL support
   - Allows for complex queries and analysis

5. Confidence scores on LLM standardization
   - Track which names were confidently standardized
   - Flag uncertain matches for manual review

6. Visualization dashboard
   - Acceptance rate trends by program
   - GPA/GRE distributions by school
   - Interactive filtering

7. Statistical analysis module
   - Correlation between metrics and acceptance
   - Program difficulty rankings
   - Year-over-year trend analysis


================================================================================
SUBMISSION CHECKLIST
================================================================================

✓ scrape.py - Web scraper using urllib and BeautifulSoup
✓ clean.py - Data cleaning module with standardization functions
✓ requirements.txt - Dependencies list (beautifulsoup4, lxml)
✓ README.txt - This comprehensive documentation
✓ README.md - Extended technical documentation
✓ robots_txt_verification.txt - Compliance evidence
✓ applicant_data.json - 30,000+ raw scraped entries
✓ applicant_data_cleaned.json - Cleaned data before LLM processing
✓ llm_hosting/ subfolder - LLM standardization code and config files
✓ GitHub repository - Private repo "jhu_software_concepts/module_2"
✓ Python 3.10+ compatible code
✓ No external API dependencies
✓ Proper error handling and logging


================================================================================
CONCLUSION
================================================================================

This assignment successfully implements a three-phase pipeline for web scraping 
and cleaning graduate school admission data. The solution demonstrates:

  • Proper use of urllib for URL management per assignment requirements
  • Effective HTML parsing with BeautifulSoup
  • Robust data standardization and cleaning techniques
  • Integration with LLM-based name standardization
  • Compliance with website robots.txt and ethical scraping practices
  • Handling of 30,000+ data entries with consistent quality

The resulting dataset is ready for downstream analysis in subsequent modules 
and provides valuable insights into graduate school admission patterns.

For detailed references and acknowledgments, see REFERENCES.txt

---
Assignment completed: [Completion Date]
Submitted by: Aaron Xu
Institution: Johns Hopkins University
Course: Modern Software Concepts
