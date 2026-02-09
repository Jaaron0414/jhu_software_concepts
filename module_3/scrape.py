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
import time
import random
from typing import List, Dict, Any, Optional
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup


def scrape_data(result_type: str = 'all', num_pages: int = 500, 
                start_page: int = 1, delay: float = 0.5) -> List[Dict[str, Any]]:
    """
    Scrape Grad Cafe pages for admission data.
    Loops through pages and extracts entry info.
    
    Args:
        result_type: 'all', 'accepted', 'rejected', 'waitlisted'
        num_pages: how many pages to scrape (each ~20 entries)
        start_page: page number to start from (for resuming)
        delay: base delay between requests in seconds (to avoid rate limiting)
        
    Returns:
        List of dicts with entry data
    """
    base_url = "https://www.thegradcafe.com/survey/index.php"
    
    # Map result types to URL parameters
    decision_map = {
        'all': '',
        'accepted': 'Accepted',
        'waitlisted': 'Wait listed',
        'rejected': 'Rejected'
    }
    
    decision_param = decision_map.get(result_type.lower(), '')
    all_data = []
    consecutive_errors = 0
    max_retries = 3
    
    print(f"Starting scraper for {result_type.upper()} results...")
    print(f"Going to try pages {start_page} to {start_page + num_pages - 1} (~{num_pages * 20} entries)")
    print(f"Delay between requests: {delay}s (with jitter)\n")
    
    for page in range(start_page, start_page + num_pages):
        retries = 0
        success = False
        
        while retries < max_retries and not success:
            try:
                # Build URL with parameters
                params = {'page': page, 'sort': 'newest'}
                if decision_param:
                    params['decision'] = decision_param
                
                query_string = urlencode(params)
                full_url = f"{base_url}?{query_string}"
                
                # Add user agent to avoid blocking
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                request = Request(full_url, headers=headers)
                
                if page % 10 == 0 or retries > 0:
                    retry_str = f" (retry {retries})" if retries > 0 else ""
                    print(f"  Scraping page {page}/{start_page + num_pages - 1}{retry_str}...", end='', flush=True)
                
                # Open URL and read response
                with urlopen(request, timeout=15) as response:
                    html_content = response.read().decode('utf-8', errors='ignore')
                
                # Parse and extract entries
                entries = _extract_entries(html_content)
                
                if not entries:
                    print(f"\n  No entries found on page {page} - probably hit the end")
                    return all_data
                
                all_data.extend(entries)
                success = True
                consecutive_errors = 0
                
                if page % 10 == 0:
                    print(f" Found {len(entries)} (Total so far: {len(all_data)})")
                
                # Add delay with jitter to be polite to the server
                sleep_time = delay + random.uniform(0, delay * 0.5)
                time.sleep(sleep_time)
                    
            except HTTPError as e:
                print(f"\n  HTTP Error on page {page}: {e.code}")
                if e.code == 404:
                    print("  Looks like we reached the end")
                    return all_data
                elif e.code == 429:  # Rate limited
                    retries += 1
                    wait_time = 30 * retries  # Exponential backoff
                    print(f"  Rate limited. Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    retries += 1
                    time.sleep(5)
                    
            except URLError as e:
                retries += 1
                consecutive_errors += 1
                print(f"\n  Connection error on page {page}: {e.reason}")
                
                if consecutive_errors >= 5:
                    print("  Too many consecutive errors. Stopping.")
                    return all_data
                
                wait_time = 10 * retries
                print(f"  Waiting {wait_time}s before retry {retries}/{max_retries}...")
                time.sleep(wait_time)
                
            except Exception as e:
                retries += 1
                print(f"\n  Something went wrong on page {page}: {e}")
                time.sleep(5)
        
        if not success:
            print(f"  Failed to scrape page {page} after {max_retries} retries. Skipping.")
            consecutive_errors += 1
            if consecutive_errors >= 5:
                print("  Too many consecutive failures. Stopping.")
                break
    
    print(f"\nTotal entries scraped: {len(all_data)}")
    return all_data


def _extract_entries(html_content: str) -> List[Dict[str, Any]]:
    """
    Extract entries from HTML page.
    Handles the new Grad Cafe HTML structure with multiple rows per entry.
    """
    entries = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the main table body
        tbody = soup.find('tbody')
        if not tbody:
            return entries
        
        rows = tbody.find_all('tr')
        
        # Process rows - entries span multiple rows
        i = 0
        while i < len(rows):
            row = rows[i]
            tds = row.find_all('td')
            
            # Main entry row has 5 columns: School, Program, Date, Decision, Actions
            if len(tds) >= 4:
                entry = _parse_main_row(row, tds)
                
                if entry:
                    # Check next rows for additional data (tags, comments)
                    j = i + 1
                    while j < len(rows):
                        next_row = rows[j]
                        next_tds = next_row.find_all('td')
                        
                        # Check if this is a continuation row (has colspan or single td)
                        if 'tw-border-none' in next_row.get('class', []):
                            # This is additional info row
                            _parse_additional_row(next_row, entry)
                            j += 1
                        else:
                            # This is a new entry row
                            break
                    
                    entries.append(entry)
                    i = j
                    continue
            
            i += 1
    
    except Exception as e:
        print(f"Error parsing HTML: {e}")
    
    return entries


def _parse_main_row(row, tds) -> Optional[Dict[str, Any]]:
    """Parse the main entry row with School, Program, Date, Decision."""
    try:
        entry = {
            'university': None,
            'program': None,
            'degree': None,
            'date': None,
            'status': None,
            'gpa': None,
            'gre_quantitative': None,
            'gre_verbal': None,
            'gre_aw': None,
            'gre_subject': None,
            'comments': None,
            'url': None,
            'entry_link': None,
            'semester_year': None,
            'international': None,
            'acceptance_date': None,
            'rejection_date': None,
        }
        
        # Extract university (first column)
        if len(tds) > 0:
            uni_div = tds[0].find('div', class_=lambda x: x and 'tw-font-medium' in x)
            if uni_div:
                entry['university'] = _clean_text(uni_div.get_text())
            else:
                entry['university'] = _clean_text(tds[0].get_text())
        
        # Extract program and degree (second column)
        if len(tds) > 1:
            program_td = tds[1]
            spans = program_td.find_all('span')
            
            if len(spans) >= 2:
                # First span is program, last span with tw-text-gray-500 is degree
                entry['program'] = _clean_text(spans[0].get_text())
                for span in spans:
                    if 'tw-text-gray-500' in span.get('class', []):
                        entry['degree'] = _clean_text(span.get_text())
            elif len(spans) == 1:
                entry['program'] = _clean_text(spans[0].get_text())
            else:
                # Fallback: parse the whole text
                text = _clean_text(program_td.get_text())
                entry['program'] = text
        
        # Extract date (third column)
        if len(tds) > 2:
            entry['date'] = _clean_text(tds[2].get_text())
        
        # Extract status/decision (fourth column)
        if len(tds) > 3:
            status_div = tds[3].find('div', class_=lambda x: x and 'tw-inline-flex' in x)
            if status_div:
                entry['status'] = _clean_text(status_div.get_text())
            else:
                entry['status'] = _clean_text(tds[3].get_text())
        
        # Extract entry link (fifth column or from any link)
        link = row.find('a', href=lambda x: x and '/result/' in x)
        if link:
            href = link.get('href')
            if href:
                if href.startswith('/'):
                    entry['entry_link'] = 'https://www.thegradcafe.com' + href
                else:
                    entry['entry_link'] = href
                # Also set url field
                entry['url'] = entry['entry_link']
        
        return entry
    
    except Exception as e:
        print(f"Error parsing main row: {e}")
        return None


def _parse_additional_row(row, entry: Dict[str, Any]) -> None:
    """Parse additional rows that contain tags (GPA, Season, etc.) or comments."""
    try:
        # Check for tag divs (GPA, Season, International/American)
        tag_divs = row.find_all('div', class_=lambda x: x and 'tw-inline-flex' in x)
        for div in tag_divs:
            text = _clean_text(div.get_text())
            if not text:
                continue
            
            # Check for semester/season (Fall 2026, Spring 2025, etc.)
            season_match = re.search(r'(Fall|Spring|Summer|Winter)\s*(\d{4})', text, re.IGNORECASE)
            if season_match:
                entry['semester_year'] = f"{season_match.group(1)} {season_match.group(2)}"
                continue
            
            # Check for international/American status
            if 'International' in text:
                entry['international'] = True
                continue
            elif 'American' in text:
                entry['international'] = False
                continue
            
            # Check for GPA
            gpa_match = re.search(r'GPA\s*(\d+\.?\d*)', text, re.IGNORECASE)
            if gpa_match:
                entry['gpa'] = gpa_match.group(1)
                continue
            
            # Check for GRE scores
            gre_match = re.search(r'GRE\s*(\d+)', text, re.IGNORECASE)
            if gre_match:
                score = int(gre_match.group(1))
                if 130 <= score <= 170:
                    # Could be verbal or quantitative
                    if 'V' in text.upper():
                        entry['gre_verbal'] = str(score)
                    elif 'Q' in text.upper():
                        entry['gre_quantitative'] = str(score)
                continue
            
            # Check for GRE AW
            aw_match = re.search(r'(?:AW|Analytical)\s*(\d+\.?\d*)', text, re.IGNORECASE)
            if aw_match:
                entry['gre_aw'] = aw_match.group(1)
                continue
        
        # Check for comments paragraph
        comment_p = row.find('p', class_=lambda x: x and 'tw-text-gray-500' in x)
        if comment_p:
            comment_text = _clean_text(comment_p.get_text())
            if comment_text and len(comment_text) > 1:
                entry['comments'] = comment_text
    
    except Exception as e:
        print(f"Error parsing additional row: {e}")


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


def _fetch_entry_details(entry_url: str, headers: dict) -> Dict[str, Any]:
    """
    Fetch detailed data from an individual result page.
    This captures GRE scores, GPA, and other details not on the list page.
    """
    details = {}
    
    try:
        request = Request(entry_url, headers=headers)
        with urlopen(request, timeout=15) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all dt/dd pairs for labeled data
        dts = soup.find_all('dt')
        for dt in dts:
            label = _clean_text(dt.get_text())
            if not label:
                continue
            
            # Find the corresponding dd
            dd = dt.find_next('dd')
            if not dd:
                continue
            
            value = _clean_text(dd.get_text())
            if not value:
                continue
            
            # Map labels to our fields
            label_lower = label.lower()
            if 'undergrad gpa' in label_lower or label_lower == 'gpa':
                details['gpa'] = value
            elif 'institution' in label_lower:
                details['university'] = value
            elif 'program' in label_lower and 'degree' not in label_lower:
                details['program'] = value
            elif 'degree type' in label_lower:
                details['degree'] = value
            elif 'decision' in label_lower:
                details['status'] = value
            elif "degree's country" in label_lower or 'country of origin' in label_lower:
                if 'international' in value.lower():
                    details['international'] = True
                elif 'american' in value.lower() or 'domestic' in value.lower():
                    details['international'] = False
            elif 'notes' in label_lower:
                details['comments'] = value
        
        # Find GRE scores in list items
        gre_items = soup.find_all('li')
        for item in gre_items:
            text = _clean_text(item.get_text())
            if not text:
                continue
            
            # GRE General (Quantitative)
            if 'gre general' in text.lower():
                match = re.search(r'(\d{2,3})', text)
                if match:
                    score = int(match.group(1))
                    if 130 <= score <= 170:
                        details['gre_quantitative'] = str(score)
            
            # GRE Verbal
            elif 'gre verbal' in text.lower():
                match = re.search(r'(\d{2,3})', text)
                if match:
                    score = int(match.group(1))
                    if 130 <= score <= 170:
                        details['gre_verbal'] = str(score)
            
            # Analytical Writing
            elif 'analytical' in text.lower() or 'writing' in text.lower():
                match = re.search(r'(\d+\.?\d*)', text)
                if match:
                    score = float(match.group(1))
                    if 0 <= score <= 6:
                        details['gre_aw'] = str(score)
    
    except Exception as e:
        # Silently fail - we'll use list page data
        pass
    
    return details


def scrape_with_details(result_type: str = 'all', num_pages: int = 500,
                        start_page: int = 1, delay: float = 0.5,
                        fetch_details: bool = False, detail_delay: float = 0.3) -> List[Dict[str, Any]]:
    """
    Scrape Grad Cafe with optional detailed fetching of individual result pages.
    
    Args:
        result_type: 'all', 'accepted', 'rejected', 'waitlisted'
        num_pages: how many pages to scrape
        start_page: page to start from
        delay: delay between list page requests
        fetch_details: whether to fetch individual result pages for GRE data
        detail_delay: delay between detail page requests
    
    Returns:
        List of entry dicts with all available data
    """
    # First, scrape the list pages
    data = scrape_data(result_type, num_pages, start_page, delay)
    
    if not fetch_details or not data:
        return data
    
    print(f"\nFetching detailed data for {len(data)} entries...")
    print("This will take a while due to rate limiting...\n")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for i, entry in enumerate(data):
        if entry.get('entry_link'):
            details = _fetch_entry_details(entry['entry_link'], headers)
            
            # Update entry with detailed data (don't overwrite existing data)
            for key, value in details.items():
                if not entry.get(key) and value:
                    entry[key] = value
            
            if (i + 1) % 100 == 0:
                print(f"  Fetched details for {i + 1}/{len(data)} entries...")
            
            # Rate limiting
            time.sleep(detail_delay + random.uniform(0, 0.2))
    
    print(f"Completed fetching details for {len(data)} entries")
    return data


def save_data(data: List[Dict[str, Any]], filename: str = 'applicant_data.json') -> str:
    """Save data to JSON file."""
    # Create dir if needed
    output_dir = os.path.dirname(filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Write JSON with UTF-8 encoding
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
        # Scrape data - 1600 pages to get 30,000+ entries
        data = scrape_data(result_type='all', num_pages=1600, delay=0.5)
        
        # Save it
        if data:
            save_data(data, 'applicant_data.json')
            
            print(f"\n--- Quick Stats ---")
            print(f"Total entries: {len(data)}")
            
            # Count field coverage
            fields = ['program', 'university', 'degree', 'status', 'gpa', 'comments', 'semester_year']
            print("\nField coverage:")
            for field in fields:
                count = sum(1 for entry in data if entry.get(field))
                pct = count / len(data) * 100 if data else 0
                print(f"  {field}: {count} ({pct:.1f}%)")
            
            print(f"\nSample entry:")
            if data:
                sample = data[0]
                for key, value in sample.items():
                    print(f"  {key}: {value}")
        else:
            print("No data scraped. Check internet connection?")
    
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
