"""
Check if we can get more details from the links
"""
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
import re

url = "https://www.thegradcafe.com/survey/index.php?action=view&result=0&page=1"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
request = Request(url, headers=headers)

with urlopen(request, timeout=10) as response:
    html = response.read().decode('utf-8', errors='ignore')

soup = BeautifulSoup(html, 'html.parser')
table = soup.find('tbody')
rows = table.find_all('tr')

print("Analyzing row structure...\n")

# Get main rows (5 cols) vs detail rows (1 col)
main_rows = [r for r in rows if len(r.find_all('td')) == 5]
detail_rows = [r for r in rows if len(r.find_all('td')) == 1]

print(f"Main rows: {len(main_rows)}")
print(f"Detail rows: {len(detail_rows)}\n")

# Show first detail row in detail
if detail_rows:
    print("=== FIRST DETAIL ROW ===")
    detail_text = detail_rows[0].get_text(strip=True)
    print(detail_text)
    print()
    
    # Try to parse it
    print("Raw text parts:")
    parts = detail_text.split()
    for part in parts[:20]:
        print(f"  {part}")

# Check for GPA/GRE patterns
print("\n\n=== Looking for data patterns ===")
for i, row in enumerate(detail_rows[:5]):
    text = row.get_text(strip=True)
    print(f"\nRow {i}: {text[:150]}")
    
    # Look for common patterns
    gpa_match = re.search(r'GPA[\s:]*(\d+\.?\d*)', text)
    gre_match = re.search(r'GRE[\s:]*(\d+)', text)
    
    if gpa_match:
        print(f"  Found GPA: {gpa_match.group(1)}")
    if gre_match:
        print(f"  Found GRE: {gre_match.group(1)}")
