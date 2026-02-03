"""
Quick diagnostic to see what we're getting from Grad Cafe
"""
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

url = "https://www.thegradcafe.com/survey/index.php?action=view&result=0&page=1"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
request = Request(url, headers=headers)

try:
    with urlopen(request, timeout=10) as response:
        html = response.read().decode('utf-8', errors='ignore')
    
    print(f"✓ Got response! ({len(html)} bytes)")
    
    # Show first 2000 characters
    print("\nFirst 2000 chars of HTML:")
    print(html[:2000])
    print("\n...")
    
    # Parse and look for table rows
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check what we find
    rows = soup.find_all('tr', class_=['even', 'odd'])
    print(f"\nFound {len(rows)} rows with class 'even' or 'odd'")
    
    # Also try without class filter
    all_rows = soup.find_all('tr')
    print(f"Total rows in page: {len(all_rows)}")
    
    # Show first row structure
    if all_rows:
        print(f"\nFirst row HTML:")
        print(all_rows[0])
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
