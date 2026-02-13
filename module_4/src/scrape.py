"""
scrape.py - Web scraper for thegradcafe.com.

Uses urllib (built-in) for HTTP requests and BeautifulSoup for
HTML parsing.  Rate-limits requests to be polite to the server.

Author: Aaron Xu
Course: JHU Modern Software Concepts
Date: February 2026
"""

import json
import os
import re
import time
import random

from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup


def scrape_data(result_type='all', num_pages=500,
                start_page=1, delay=0.5):
    """Scrape Grad Cafe list pages and return a list of entry dicts.

    Each page has ~20 entries.  We stop early if a page comes back
    empty or we hit too many consecutive errors.
    """
    base_url = "https://www.thegradcafe.com/survey/index.php"
    decision_map = {
        'all': '',
        'accepted': 'Accepted',
        'waitlisted': 'Wait listed',
        'rejected': 'Rejected',
    }
    decision = decision_map.get(result_type.lower(), '')
    all_data = []
    errors = 0

    for page in range(start_page, start_page + num_pages):
        try:
            params = {'page': page, 'sort': 'newest'}
            if decision:
                params['decision'] = decision
            url = f"{base_url}?{urlencode(params)}"
            headers = {
                'User-Agent': 'Mozilla/5.0 GradCafeScraper/1.0'
            }
            req = Request(url, headers=headers)

            with urlopen(req, timeout=15) as resp:
                html = resp.read().decode('utf-8', errors='ignore')

            entries = extract_entries(html)
            if not entries:
                break

            all_data.extend(entries)
            errors = 0
            time.sleep(delay + random.uniform(0, delay * 0.5))

        except HTTPError as exc:
            if exc.code == 404:
                break
            errors += 1
            if errors >= 5:
                break
            time.sleep(5)

        except (URLError, Exception):
            errors += 1
            if errors >= 5:
                break
            time.sleep(5)

    return all_data


def extract_entries(html):
    """Parse a Grad Cafe list page and pull out individual entries."""
    entries = []
    soup = BeautifulSoup(html, 'html.parser')
    tbody = soup.find('tbody')
    if not tbody:
        return entries

    rows = tbody.find_all('tr')
    i = 0
    while i < len(rows):
        tds = rows[i].find_all('td')
        if len(tds) >= 4:
            entry = parse_main_row(rows[i], tds)
            if entry:
                j = i + 1
                while (j < len(rows)
                       and 'tw-border-none'
                       in rows[j].get('class', [])):
                    parse_additional_row(rows[j], entry)
                    j += 1
                entries.append(entry)
                i = j
                continue
        i += 1

    return entries


def parse_main_row(row, tds):
    """Pull university, program, degree, status, and link from the main row."""
    entry = {
        'university': None, 'program': None, 'degree': None,
        'date': None, 'status': None, 'gpa': None,
        'gre_quantitative': None, 'gre_verbal': None,
        'gre_aw': None, 'comments': None, 'url': None,
        'entry_link': None, 'semester_year': None,
        'international': None,
    }

    # University (first column)
    uni_div = tds[0].find(
        'div', class_=lambda x: x and 'tw-font-medium' in x
    )
    if uni_div:
        entry['university'] = clean_text(uni_div.get_text())
    else:
        entry['university'] = clean_text(tds[0].get_text())

    # Program and degree (second column)
    spans = tds[1].find_all('span')
    if spans:
        entry['program'] = clean_text(spans[0].get_text())
        for span in spans:
            if 'tw-text-gray-500' in span.get('class', []):
                entry['degree'] = clean_text(span.get_text())
    else:
        entry['program'] = clean_text(tds[1].get_text())

    # Date (third column)
    entry['date'] = clean_text(tds[2].get_text())

    # Status (fourth column)
    status_div = tds[3].find(
        'div', class_=lambda x: x and 'tw-inline-flex' in x
    )
    if status_div:
        entry['status'] = clean_text(status_div.get_text())
    else:
        entry['status'] = clean_text(tds[3].get_text())

    # Entry link
    link = row.find('a', href=lambda x: x and '/result/' in x)
    if link and link.get('href'):
        href = link['href']
        if href.startswith('/'):
            entry['entry_link'] = (
                'https://www.thegradcafe.com' + href
            )
        else:
            entry['entry_link'] = href
        entry['url'] = entry['entry_link']

    return entry


def parse_additional_row(row, entry):
    """Parse the extra rows that hold tags (GPA, season, GRE) and comments."""
    tag_divs = row.find_all(
        'div', class_=lambda x: x and 'tw-inline-flex' in x
    )
    for div in tag_divs:
        text = clean_text(div.get_text())
        if not text:
            continue

        season = re.search(
            r'(Fall|Spring|Summer|Winter)\s*(\d{4})',
            text, re.IGNORECASE
        )
        if season:
            entry['semester_year'] = (
                f"{season.group(1)} {season.group(2)}"
            )
            continue

        if 'International' in text:
            entry['international'] = True
            continue
        if 'American' in text:
            entry['international'] = False
            continue

        gpa = re.search(r'GPA\s*(\d+\.?\d*)', text, re.IGNORECASE)
        if gpa:
            entry['gpa'] = gpa.group(1)
            continue

        gre = re.search(r'GRE\s*\w?\s*(\d+)', text, re.IGNORECASE)
        if gre:
            score = int(gre.group(1))
            if 130 <= score <= 170:
                if 'V' in text.upper():
                    entry['gre_verbal'] = str(score)
                elif 'Q' in text.upper():
                    entry['gre_quantitative'] = str(score)
            continue

        aw = re.search(
            r'(?:AW|Analytical)\s*(\d+\.?\d*)', text, re.IGNORECASE
        )
        if aw:
            entry['gre_aw'] = aw.group(1)
            continue

    comment_p = row.find(
        'p', class_=lambda x: x and 'tw-text-gray-500' in x
    )
    if comment_p:
        text = clean_text(comment_p.get_text())
        if text and len(text) > 1:
            entry['comments'] = text


def clean_text(text):
    """Strip HTML tags and collapse whitespace. Returns None for empty."""
    if not text:
        return None
    text = re.sub(r'<[^>]+>', '', text)
    text = ' '.join(text.split()).strip()
    return text if text else None


def save_data(data, filename='applicant_data.json'):
    """Dump data to a JSON file (creates parent dirs if needed)."""
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    with open(filename, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    return filename


def load_data(filename='applicant_data.json'):
    """Load data from a JSON file. Returns [] if the file is missing."""
    if not os.path.exists(filename):
        return []
    with open(filename, 'r', encoding='utf-8') as fh:
        return json.load(fh)
