"""
Grad Cafe Web Scraper
Scrapes grad school acceptance data from https://www.thegradcafe.com
Uses urllib (built-in) + BeautifulSoup for parsing

Main functions:
- scrape_data(): pulls pages and extracts entries
- save_data(): saves to JSON
- load_data(): loads from JSON
"""

import os
import json
import re
from typing import List, Dict, Any, Optional
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup


def scrape_data(result_type: str = 'all', num_pages: int = 500) -> List[Dict[str, Any]]:
    """
    Scrape Grad Cafe pages for admission data.
    Loops through pages and extracts entry info.
    
    Args:
        result_type: 'all', 'accepted', 'rejected', 'waitlisted'
        num_pages: how many pages to scrape (each ~20 entries)
        
    Returns:
        List of dicts with entry data
    """
    base_url = "https://www.thegradcafe.com/survey/index.php"
    
    result_map = {
        'all': 0,
        'accepted': 1,
        'waitlisted': 2,
        'rejected': 3
    }
    
    result_code = result_map.get(result_type.lower(), 0)
    all_data = []
    
    print(f"Starting scraper for {result_type.upper()} results...")
    print(f"Going to try {num_pages} pages (~{num_pages * 20} entries)\n")
    
    for page in range(1, num_pages + 1):
        try:
            # build the URL with params
            params = {
                'action': 'view',
                'result': result_code,
                'page': page
            }
            
            query_string = urlencode(params)
            full_url = f"{base_url}?{query_string}"
            
            # add user agent so we don't get blocked
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            request = Request(full_url, headers=headers)
            
            if page % 10 == 0:
                print(f"  Scraping page {page}/{num_pages}...", end='', flush=True)
            
            # Open URL and read response
            with urlopen(request, timeout=10) as response:
                html_content = response.read().decode('utf-8', errors='ignore')
            
            # Parse and extract entries
            entries = _extract_entries(html_content)
            
            if not entries:
                print(f"\n  No entries found on page {page} - probably hit the end")
                break
            
            all_data.extend(entries)
            
            if page % 10 == 0:
                print(f" Found {len(entries)} (Total so far: {len(all_data)})")
                
        except HTTPError as e:
            print(f"\n  HTTP Error on page {page}: {e.code}")
            if e.code == 404:
                print("  Looks like we reached the end")
                break
        except URLError as e:
            print(f"\n  Connection error on page {page}: {e.reason}")
            break
        except Exception as e:
            print(f"\n  Something went wrong on page {page}: {e}")
            continue
    
    print(f"\nTotal entries scraped: {len(all_data)}")
    return all_data


def _extract_entries(html_content: str) -> List[Dict[str, Any]]:
    """
    Extract entries from HTML page.
    Finds table rows with applicant data and their detail rows.
    """
    entries = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the main table - look for tbody
        table = soup.find('tbody')
        if table:
            rows = table.find_all('tr')
        else:
            all_rows = soup.find_all('tr')
            rows = all_rows[1:] if len(all_rows) > 1 else []
        
        # Process rows - main rows have 5 cols, detail rows have 1 col
        i = 0
        while i < len(rows):
            row = rows[i]
            cols = row.find_all('td')
            
            # Check if this is a main row (5 columns)
            if len(cols) == 5:
                entry = {
                    'date': _clean_text(cols[2].text) if len(cols) > 2 else None,
                    'status': _clean_text(cols[3].text) if len(cols) > 3 else None,
                    'degree': None,
                    'program': _clean_text(cols[1].text) if len(cols) > 1 else None,
                    'university': _clean_text(cols[0].text) if len(cols) > 0 else None,
                    'gpa': None,
                    'gre_quantitative': None,
                    'gre_verbal': None,
                    'gre_aw': None,
                    'comments': None,
                    'url': None,
                    'entry_link': None,
                    'gre_subject': None,
                    'acceptance_date': None,
                    'rejection_date': None,
                    'semester_year': None,
                    'international': None,
                }
                
                # Extract degree from program if possible
                program_text = entry.get('program', '')
                if 'PhD' in program_text.upper():
                    entry['degree'] = 'PhD'
                elif 'MS' in program_text.upper() or 'Master' in program_text:
                    entry['degree'] = 'MS'
                elif 'MBA' in program_text.upper():
                    entry['degree'] = 'MBA'
                
                # Try to get the entry link
                link = cols[4].find('a', href=True)
                if link:
                    href = link.get('href')
                    if href:
                        entry['entry_link'] = 'https://www.thegradcafe.com' + href if href.startswith('/') else href
                
                # Check if next row is a detail row (1 col)
                if i + 1 < len(rows):
                    next_row = rows[i + 1]
                    next_cols = next_row.find_all('td')
                    
                    if len(next_cols) == 1:
                        # This is a detail row - parse it
                        detail_text = _clean_text(next_cols[0].text)
                        if detail_text:
                            _parse_detail_row(detail_text, entry)
                        i += 1  # Skip the detail row next iteration
                
                entries.append(entry)
            
            i += 1
    
    except Exception as e:
        print(f"Error parsing HTML: {e}")
    
    return entries


def _parse_detail_row(detail_text: str, entry: Dict[str, Any]) -> None:
    """
    Parse detail row to extract additional info.
    Format: "Status [Date] Term International/American [GPA X.XX] [other info]"
    """
    if not detail_text:
        return
    
    # Extract semester/year (Fall 2026, Spring 2025, etc)
    semester_match = re.search(r'(Fall|Spring|Summer|Winter)\s+(\d{4})', detail_text)
    if semester_match:
        entry['semester_year'] = f"{semester_match.group(1)} {semester_match.group(2)}"
    
    # Extract international status
    if 'International' in detail_text:
        entry['international'] = True
    elif 'American' in detail_text:
        entry['international'] = False
    
    # Extract GPA
    gpa_match = re.search(r'GPA[\s:]*(\d+\.?\d*)', detail_text)
    if gpa_match:
        entry['gpa'] = gpa_match.group(1)
    
    # Extract GRE scores (look for patterns like "GRE 160/170" or similar)
    gre_match = re.search(r'GRE[\s:]*(\d+)\s*[/\s]+(\d+)', detail_text)
    if gre_match:
        # Could be Q/V or V/Q depending on order, try to detect
        score1, score2 = int(gre_match.group(1)), int(gre_match.group(2))
        # GRE scores: V and Q are 130-170, AW is 0-6
        if 130 <= score1 <= 170 and 130 <= score2 <= 170:
            entry['gre_verbal'] = str(score1)
            entry['gre_quantitative'] = str(score2)


def _extract_url(row) -> Optional[str]:
    """Get entry URL from table row."""
    try:
        link = row.find('a', href=True)
        if link:
            href = link.get('href')
            if href:
                if href.startswith('/'):
                    return 'https://www.thegradcafe.com' + href
                elif href.startswith('http'):
                    return href
    except:
        pass
    
    return None


def _extract_entry_link(row) -> Optional[str]:
    """Get the forum discussion link."""
    try:
        links = row.find_all('a', href=True)
        for link in links:
            href = link.get('href')
            if href and 'viewforum' in href:
                if href.startswith('/'):
                    return 'https://www.thegradcafe.com' + href
                return href
    except:
        pass
    
    return None


def _clean_text(text: str) -> Optional[str]:
    """
    Clean text from HTML.
    Remove tags, extra spaces, etc.
    """
    if not text:
        return None
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    text = text.strip()
    
    if not text:
        return None
    
    return text


def save_data(data: List[Dict[str, Any]], filename: str = 'applicant_data.json') -> str:
    """Save data to JSON file."""
    # Create dir if needed
    output_dir = os.path.dirname(filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(data)} entries to {filename}")
    return filename


def load_data(filename: str = 'applicant_data.json') -> List[Dict[str, Any]]:
    """Load data from JSON file."""
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return []
    
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} entries from {filename}")
    return data


def main():
    """Main function - run the scraper."""
    try:
        # Scrape data
        # Note: Using smaller num for testing, bump to ~1500 for full 30k entries
        data = scrape_data(result_type='all', num_pages=100)
        
        # Save it
        if data:
            save_data(data, 'applicant_data.json')
            
            print(f"\n--- Quick Stats ---")
            print(f"Total entries: {len(data)}")
            print(f"\nSample entry:")
            if data:
                sample = data[0]
                print(f"  Program: {sample.get('program')}")
                print(f"  Status: {sample.get('status')}")
                print(f"  Degree: {sample.get('degree')}")
                print(f"  GPA: {sample.get('gpa')}")
        else:
            print("No data scraped. Check internet connection?")
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
