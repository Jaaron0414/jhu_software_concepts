"""
clean.py - Data cleaning and standardisation module

Provides functions to clean raw Grad Cafe applicant data:
  - Standardise GPA, GRE scores, dates
  - Separate program and university names
  - Remove residual HTML
  - Standardise status labels

Author: Student
Date: February 2026
"""

import json
import os
import re
from datetime import datetime


def clean_data(raw_data, use_llm=False):
    """Clean a list of raw applicant dicts.

    Args:
        raw_data: List of dicts from the scraper.
        use_llm: If True, print a reminder about LLM cleaning.

    Returns:
        list[dict]: Cleaned applicant records.
    """
    cleaned = []

    for entry in raw_data:
        try:
            cleaned_entry = {
                'program': entry.get('program'),
                'university': entry.get('university'),
                'degree': entry.get('degree'),
                'status': clean_status(entry.get('status')),
                'date_added': parse_date(entry.get('date')),
                'gpa': standardize_gpa(entry.get('gpa')),
                'gre_verbal': standardize_gre(entry.get('gre_verbal')),
                'gre_quantitative': standardize_gre(
                    entry.get('gre_quantitative')
                ),
                'gre_aw': standardize_gre(entry.get('gre_aw')),
                'comments': remove_html(entry.get('comments')),
                'url': entry.get('url'),
                'entry_link': entry.get('entry_link'),
                'international': entry.get('international'),
                'semester_year': entry.get('semester_year'),
            }
            cleaned.append(cleaned_entry)
        except Exception:
            continue

    if use_llm:
        print("Run LLM standardization separately via llm_hosting/.")

    return cleaned


def parse_program_university(text):
    """Split a combined program/university string.

    Tries patterns: 'X at Y', 'X (Y)', 'X, Y'.

    Args:
        text: Combined string, or None.

    Returns:
        (program, university) tuple; either may be None.
    """
    if not text:
        return None, None

    text = text.strip()

    match = re.search(r'(.+?)\s+at\s+(.+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    match = re.search(r'(.+?)\s*\((.+?)\)', text)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    if ',' in text:
        parts = text.split(',', 1)
        return parts[0].strip(), parts[1].strip()

    return text, None


def standardize_gre(score):
    """Clean a GRE score string, returning digits or None.

    Args:
        score: Raw score string.

    Returns:
        str of digits or None.
    """
    if not score or not isinstance(score, str):
        return None
    digits = re.sub(r'[^\d]', '', score.strip())
    if not digits:
        return None
    val = int(digits)
    if 0 <= val <= 800:
        return str(val)
    return None


def standardize_gpa(gpa):
    """Clean a GPA value, returning a formatted string or None.

    Args:
        gpa: Raw GPA string.

    Returns:
        str like '3.95' or None.
    """
    if not gpa or not isinstance(gpa, str):
        return None
    match = re.search(r'(\d+\.?\d*)', gpa.strip())
    if match:
        val = float(match.group(1))
        if 0 <= val <= 4.0:
            return f"{val:.2f}"
    return None


def clean_status(status):
    """Standardise an admission status string.

    Args:
        status: Raw status text.

    Returns:
        One of 'Accepted', 'Rejected', 'Waitlisted', or the
        original (stripped) string.
    """
    if not status:
        return None
    upper = status.upper().strip()
    if 'ACCEPT' in upper:
        return 'Accepted'
    if 'REJECT' in upper:
        return 'Rejected'
    if 'WAITLIST' in upper:
        return 'Waitlisted'
    return status.strip()


def parse_date(date_str):
    """Convert a date string to ISO format (YYYY-MM-DD).

    Supports MM/DD/YYYY and YYYY-MM-DD.

    Args:
        date_str: Raw date string.

    Returns:
        str in ISO format, or None.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()

    # MM/DD/YYYY
    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if match:
        try:
            m, d, y = (int(x) for x in match.groups())
            return datetime(y, m, d).strftime('%Y-%m-%d')
        except ValueError:
            pass

    # YYYY-MM-DD
    match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
    if match:
        try:
            y, m, d = (int(x) for x in match.groups())
            return datetime(y, m, d).strftime('%Y-%m-%d')
        except ValueError:
            pass

    return None


def remove_html(text):
    """Strip HTML tags and entities from *text*.

    Args:
        text: Raw text that may contain HTML.

    Returns:
        Cleaned string, or None.
    """
    if not text:
        return None
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    text = ' '.join(text.split()).strip()
    return text if text else None


def save_cleaned_data(data, filename='applicant_data_cleaned.json'):
    """Write cleaned data to a JSON file.

    Args:
        data: Cleaned applicant list.
        filename: Destination path.

    Returns:
        str: The filename written.
    """
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    with open(filename, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    return filename


def load_cleaned_data(filename='applicant_data_cleaned.json'):
    """Load cleaned data from a JSON file.

    Args:
        filename: Path to JSON file.

    Returns:
        list: Parsed data, or empty list if missing.
    """
    if not os.path.exists(filename):
        return []
    with open(filename, 'r', encoding='utf-8') as fh:
        return json.load(fh)
