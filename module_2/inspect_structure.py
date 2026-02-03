"""
Deep dive into the HTML structure to find all available fields
"""
from urllib.request import urlopen, Request
from bs4 import BeautifulSoup

url = "https://www.thegradcafe.com/survey/index.php?action=view&result=0&page=1"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
request = Request(url, headers=headers)

try:
    with urlopen(request, timeout=10) as response:
        html = response.read().decode('utf-8', errors='ignore')
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find tbody
    table = soup.find('tbody')
    if table:
        rows = table.find_all('tr')
        print(f"Found {len(rows)} rows in tbody\n")
        
        # Show first 2 data rows (skip header)
        for i, row in enumerate(rows[:3]):
            print(f"\n=== ROW {i} ===")
            cols = row.find_all('td')
            print(f"Total columns: {len(cols)}")
            
            for j, col in enumerate(cols):
                text = col.get_text(strip=True)[:100]  # First 100 chars
                print(f"  Col {j}: {text}")
            
            # Show full HTML for first row
            if i == 0:
                print("\n=== Full HTML of first row ===")
                print(row.prettify()[:2000])

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
