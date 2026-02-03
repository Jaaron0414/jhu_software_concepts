#!/usr/bin/env python3
"""Check if the assignment meets all requirements"""

import json
import os
from scrape import scrape_data
from clean import clean_data

print("=" * 70)
print("ASSIGNMENT REQUIREMENTS CHECKLIST")
print("=" * 70)

# 1. File check
print("\n1. REQUIRED FILES:")
files_required = {
    'scrape.py': 'Web scraper using urllib',
    'clean.py': 'Data cleaning module',
    'requirements.txt': 'Dependencies list',
    'README.txt': 'Documentation',
    'applicant_data.json': 'Raw scraped data (30,000+ entries)',
    'REFERENCES.txt': 'Acknowledgments'
}

for f, desc in files_required.items():
    exists = os.path.exists(f)
    status = "✓" if exists else "✗"
    print(f"   {status} {f} - {desc}")

# 2. Check scrape.py uses urllib
print("\n2. SCRAPE.PY REQUIREMENTS:")
with open('scrape.py') as f:
    scrape_code = f.read()
    
checks = {
    'urllib.request': 'urllib import' in scrape_code,
    'urllib.parse': 'urlencode' in scrape_code or 'urllib.parse' in scrape_code,
    'BeautifulSoup': 'BeautifulSoup' in scrape_code,
    'JSON output': 'json.dump' in scrape_code or 'save_data' in scrape_code,
    'Error handling': 'except' in scrape_code and 'HTTPError' in scrape_code
}

for req, met in checks.items():
    status = "✓" if met else "✗"
    print(f"   {status} {req}")

# 3. Check dependencies
print("\n3. DEPENDENCIES:")
with open('requirements.txt') as f:
    reqs = f.read()
    
deps = {
    'beautifulsoup4': 'beautifulsoup4' in reqs,
    'lxml': 'lxml' in reqs,
    'urllib': 'Built-in (no entry needed)'
}

for dep, met in deps.items():
    if 'Built-in' in str(met):
        print(f"   ✓ {dep} - {met}")
    else:
        status = "✓" if met else "✗"
        print(f"   {status} {dep}")

# 4. Check data format
print("\n4. DATA FORMAT:")
if os.path.exists('applicant_data.json'):
    with open('applicant_data.json') as f:
        try:
            data = json.load(f)
            print(f"   ✓ JSON format")
            print(f"   ✓ Total entries: {len(data)}")
            
            if len(data) > 30000:
                print(f"   ✓ Meets 30,000+ entries requirement")
            else:
                print(f"   ✗ Only {len(data)} entries (target: 30,000+)")
            
            # Check fields
            sample = data[0]
            required_fields = [
                'date', 'status', 'program', 'university', 'degree',
                'gpa', 'gre_verbal', 'gre_quantitative'
            ]
            
            print(f"\n   Required fields present:")
            for field in required_fields:
                present = field in sample
                status = "✓" if present else "✗"
                print(f"      {status} {field}")
        except json.JSONDecodeError:
            print(f"   ✗ Invalid JSON format")
else:
    print(f"   ✗ applicant_data.json not found")

# 5. Check Python version compatibility
print("\n5. PYTHON VERSION:")
import sys
version = sys.version_info
if version.major >= 3 and version.minor >= 10:
    print(f"   ✓ Python {version.major}.{version.minor} (requires 3.10+)")
else:
    print(f"   ✗ Python {version.major}.{version.minor} (requires 3.10+)")

# 6. Check clean.py functions
print("\n6. CLEAN.PY FUNCTIONS:")
with open('clean.py') as f:
    clean_code = f.read()

clean_functions = {
    'clean_data()': 'def clean_data(' in clean_code,
    '_standardize_gpa()': 'def _standardize_gpa(' in clean_code,
    '_standardize_gre_score()': 'def _standardize_gre_score(' in clean_code,
    '_parse_date()': 'def _parse_date(' in clean_code,
    '_clean_status()': 'def _clean_status(' in clean_code,
}

for func, present in clean_functions.items():
    status = "✓" if present else "✗"
    print(f"   {status} {func}")

# 7. Documentation
print("\n7. DOCUMENTATION:")
docs = {
    'README.txt': os.path.exists('README.txt'),
    'README.md': os.path.exists('README.md'),
    'REFERENCES.txt': os.path.exists('REFERENCES.txt'),
    'robots.txt verification': os.path.exists('robots_txt_verification.txt')
}

for doc, exists in docs.items():
    status = "✓" if exists else "✗"
    print(f"   {status} {doc}")

print("\n" + "=" * 70)
print("SUMMARY: Assignment structure appears complete")
print("=" * 70)
