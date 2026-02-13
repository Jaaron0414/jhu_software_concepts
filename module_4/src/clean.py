"""
clean.py - Data cleaning and standardization.

Takes raw scraped data and normalizes it: cleans GPA/GRE values,
converts dates to ISO format, strips leftover HTML, and
standardizes status labels (Accepted/Rejected/Waitlisted).

Author: Jie Xu
Course: JHU Modern Software Concepts
Date: February 2026
"""

import json
import os
import re
from datetime import datetime


def clean_data(raw_data, use_llm=False):
    """Run all cleaning steps on a list of raw applicant dicts."""
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
    """Try to split 'Program at University' or 'Program, University'."""
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
    """Extract digits from a GRE score string. Returns None if invalid."""
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
    """Parse a GPA string and format it to two decimals (0-4.0 range)."""
    if not gpa or not isinstance(gpa, str):
        return None
    match = re.search(r'(\d+\.?\d*)', gpa.strip())
    if match:
        val = float(match.group(1))
        if 0 <= val <= 4.0:
            return f"{val:.2f}"
    return None


def clean_status(status):
    """Map raw status text to Accepted / Rejected / Waitlisted."""
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
    """Convert MM/DD/YYYY or YYYY-MM-DD to ISO format. Returns None on failure."""
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
    """Strip HTML tags and decode common entities."""
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
    """Dump cleaned data to JSON."""
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    with open(filename, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    return filename


def load_cleaned_data(filename='applicant_data_cleaned.json'):
    """Load cleaned data from JSON. Returns [] if missing."""
    if not os.path.exists(filename):
        return []
    with open(filename, 'r', encoding='utf-8') as fh:
        return json.load(fh)
