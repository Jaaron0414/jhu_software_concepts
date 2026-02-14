"""Web scraper for thegradcafe.com admission results.

Uses only ``urllib`` (built-in) for HTTP requests and ``BeautifulSoup``
for HTML parsing.  Rate-limits requests with configurable delays to
be polite to the Grad Cafe server.

Author: Jie Xu
Course: JHU Modern Software Concepts
Date: February 2026
"""

from __future__ import annotations

import json
import os
import re
import time
import random
from typing import Optional

from urllib.request import urlopen, Request
from urllib.parse import urlencode
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Main scraper function
# ---------------------------------------------------------------------------

def scrape_data(result_type: str = 'all',
                num_pages: int = 500,
                start_page: int = 1,
                delay: float = 0.5) -> list[dict]:
    """Scrape Grad Cafe list pages and return parsed entries.

    Iterates through paginated result pages, extracting applicant
    data from the HTML table.  Stops early when a page comes back
    empty (no more data) or after 5 consecutive network errors.

    Args:
        result_type: Filter — ``'all'``, ``'accepted'``,
            ``'rejected'``, or ``'waitlisted'``.
        num_pages: Maximum number of pages to request.
        start_page: Page number to begin from (1-indexed).
        delay: Base delay in seconds between requests.

    Returns:
        A list of applicant dicts, one per entry found.
    """
    base_url = "https://www.thegradcafe.com/survey/index.php"

    # Map friendly names to the query-parameter values Grad Cafe expects
    decision_map = {
        'all': '',
        'accepted': 'Accepted',
        'waitlisted': 'Wait listed',
        'rejected': 'Rejected',
    }
    decision = decision_map.get(result_type.lower(), '')

    all_data: list[dict] = []
    errors = 0  # consecutive-error counter

    for page in range(start_page, start_page + num_pages):
        try:
            params: dict = {'page': page, 'sort': 'newest'}
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
                break  # empty page means we've exhausted all results

            all_data.extend(entries)
            errors = 0  # reset the error counter after a successful page

            # Be polite: sleep between requests (with small random jitter)
            time.sleep(delay + random.uniform(0, delay * 0.5))

        except HTTPError as exc:
            if exc.code == 404:
                break  # no more pages exist
            errors += 1
            if errors >= 5:
                break  # too many consecutive server errors
            time.sleep(5)

        except (URLError, Exception):
            errors += 1
            if errors >= 5:
                break
            time.sleep(5)

    return all_data


# ---------------------------------------------------------------------------
# HTML parsing
# ---------------------------------------------------------------------------

def extract_entries(html: str) -> list[dict]:
    """Parse a single Grad Cafe list page into applicant dicts.

    The page has an HTML ``<table>`` where each applicant occupies a
    main ``<tr>`` (university, program, status) followed by zero or
    more continuation rows (tags, scores, comments) that have the
    CSS class ``tw-border-none``.

    Args:
        html: Raw HTML of one Grad Cafe list page.

    Returns:
        A list of parsed applicant dicts.
    """
    entries: list[dict] = []
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
                # Consume continuation rows (same applicant)
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


def parse_main_row(row, tds) -> Optional[dict]:
    """Extract core fields from the primary ``<tr>`` of an entry.

    Columns (left to right):
      0 — University name
      1 — Program name + degree badge
      2 — Date
      3 — Admission status
      4 — (optional) Link to the full entry page

    Args:
        row: The ``<tr>`` BeautifulSoup tag.
        tds: Pre-extracted list of ``<td>`` tags from the row.

    Returns:
        A dict with all core fields initialized.
    """
    entry: dict = {
        'university': None, 'program': None, 'degree': None,
        'date': None, 'status': None, 'gpa': None,
        'gre_quantitative': None, 'gre_verbal': None,
        'gre_aw': None, 'comments': None, 'url': None,
        'entry_link': None, 'semester_year': None,
        'international': None,
    }

    # Column 0 — University name (sometimes inside a styled div)
    uni_div = tds[0].find(
        'div', class_=lambda x: x and 'tw-font-medium' in x
    )
    if uni_div:
        entry['university'] = clean_text(uni_div.get_text())
    else:
        entry['university'] = clean_text(tds[0].get_text())

    # Column 1 — Program + optional degree badge (gray span)
    spans = tds[1].find_all('span')
    if spans:
        entry['program'] = clean_text(spans[0].get_text())
        for span in spans:
            if 'tw-text-gray-500' in span.get('class', []):
                entry['degree'] = clean_text(span.get_text())
    else:
        entry['program'] = clean_text(tds[1].get_text())

    # Column 2 — Date
    entry['date'] = clean_text(tds[2].get_text())

    # Column 3 — Status (inside a styled inline-flex div)
    status_div = tds[3].find(
        'div', class_=lambda x: x and 'tw-inline-flex' in x
    )
    if status_div:
        entry['status'] = clean_text(status_div.get_text())
    else:
        entry['status'] = clean_text(tds[3].get_text())

    # Column 4 (optional) — Link to full entry
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


def parse_additional_row(row, entry: dict) -> None:
    """Parse continuation rows that hold tags, scores, and comments.

    These rows have the CSS class ``tw-border-none`` and contain
    small tag-like divs for semester, nationality, GPA, GRE scores,
    and a paragraph for user comments.

    Args:
        row: A continuation ``<tr>`` tag.
        entry: The applicant dict being built (modified in place).
    """
    tag_divs = row.find_all(
        'div', class_=lambda x: x and 'tw-inline-flex' in x
    )
    for div in tag_divs:
        text = clean_text(div.get_text())
        if not text:
            continue

        # Semester / year tag (e.g. "Fall 2026")
        season = re.search(
            r'(Fall|Spring|Summer|Winter)\s*(\d{4})',
            text, re.IGNORECASE
        )
        if season:
            entry['semester_year'] = (
                f"{season.group(1)} {season.group(2)}"
            )
            continue

        # Nationality tag
        if 'International' in text:
            entry['international'] = True
            continue
        if 'American' in text:
            entry['international'] = False
            continue

        # GPA tag (e.g. "GPA 3.95")
        gpa = re.search(r'GPA\s*(\d+\.?\d*)', text, re.IGNORECASE)
        if gpa:
            entry['gpa'] = gpa.group(1)
            continue

        # GRE tag (e.g. "GRE Q 170", "GRE V 165")
        # The \w? allows an optional single-letter qualifier (Q or V)
        gre = re.search(r'GRE\s*\w?\s*(\d+)', text, re.IGNORECASE)
        if gre:
            score = int(gre.group(1))
            if 130 <= score <= 170:  # valid new-GRE section range
                if 'V' in text.upper():
                    entry['gre_verbal'] = str(score)
                elif 'Q' in text.upper():
                    entry['gre_quantitative'] = str(score)
            continue

        # Analytical Writing tag (e.g. "AW 5.0")
        aw = re.search(
            r'(?:AW|Analytical)\s*(\d+\.?\d*)', text, re.IGNORECASE
        )
        if aw:
            entry['gre_aw'] = aw.group(1)
            continue

    # User comment paragraph (gray text below the tag row)
    comment_p = row.find(
        'p', class_=lambda x: x and 'tw-text-gray-500' in x
    )
    if comment_p:
        text = clean_text(comment_p.get_text())
        if text and len(text) > 1:
            entry['comments'] = text


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def clean_text(text: Optional[str]) -> Optional[str]:
    """Strip HTML tags and collapse whitespace.

    Args:
        text: Raw text (may be ``None``).

    Returns:
        Cleaned string, or ``None`` if the result is empty.
    """
    if not text:
        return None
    text = re.sub(r'<[^>]+>', '', text)
    text = ' '.join(text.split()).strip()
    return text if text else None


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def save_data(data: list, filename: str = 'applicant_data.json') -> str:
    """Write data to a JSON file, creating directories as needed.

    Args:
        data: Serializable Python object.
        filename: Destination path.

    Returns:
        The filename that was written.
    """
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    with open(filename, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    return filename


def load_data(filename: str = 'applicant_data.json') -> list:
    """Load data from a JSON file.

    Args:
        filename: Path to the JSON file.

    Returns:
        Parsed data, or ``[]`` if the file does not exist.
    """
    if not os.path.exists(filename):
        return []
    with open(filename, 'r', encoding='utf-8') as fh:
        return json.load(fh)
