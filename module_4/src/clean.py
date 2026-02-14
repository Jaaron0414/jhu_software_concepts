"""Data cleaning and standardization for Grad Cafe records.

Takes raw scraped data and normalizes it:
  - Cleans GPA / GRE score strings into consistent numeric formats
  - Converts dates to ISO-8601 (``YYYY-MM-DD``)
  - Strips leftover HTML tags and decodes common entities
  - Standardizes admission status labels (Accepted / Rejected / Waitlisted)

Author: Jie Xu
Course: JHU Modern Software Concepts
Date: February 2026
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Top-level cleaning function
# ---------------------------------------------------------------------------

def clean_data(raw_data: list[dict],
               use_llm: bool = False) -> list[dict]:
    """Apply all cleaning steps to a list of raw applicant dicts.

    Each entry goes through status normalization, date parsing,
    GPA/GRE standardization, and HTML removal.  Entries that raise
    any exception (e.g. ``None`` items) are silently skipped.

    Args:
        raw_data: List of dicts straight from the scraper.
        use_llm: If ``True``, prints a reminder about the LLM
            cleaning step (run separately).

    Returns:
        A new list of cleaned applicant dicts.
    """
    cleaned: list[dict] = []

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
            # Skip malformed entries rather than crashing the whole batch
            continue

    if use_llm:
        print("Run LLM standardization separately via llm_hosting/.")

    return cleaned


# ---------------------------------------------------------------------------
# Field-level helpers
# ---------------------------------------------------------------------------

def parse_program_university(text: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Split a combined program / university string.

    Tries three common formats found on Grad Cafe:
      - ``'CS at MIT'``  (separated by " at ")
      - ``'CS (MIT)'``   (parenthesized university)
      - ``'CS, MIT'``    (comma-separated)

    Args:
        text: The raw combined string, or ``None``.

    Returns:
        A ``(program, university)`` tuple; either may be ``None``.
    """
    if not text:
        return None, None

    text = text.strip()

    # Pattern 1: "X at Y"
    match = re.search(r'(.+?)\s+at\s+(.+)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # Pattern 2: "X (Y)"
    match = re.search(r'(.+?)\s*\((.+?)\)', text)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # Pattern 3: "X, Y"
    if ',' in text:
        parts = text.split(',', 1)
        return parts[0].strip(), parts[1].strip()

    # Fallback: treat entire string as the program name
    return text, None


def standardize_gre(score: Optional[str]) -> Optional[str]:
    """Extract a numeric GRE score from a raw string.

    Strips non-digit characters, then validates the result falls
    within the 0-800 range (covers both old and new GRE scales).

    Args:
        score: Raw score string like ``'165'`` or ``'170pts'``.

    Returns:
        A digit-only string, or ``None`` if invalid.
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


def standardize_gpa(gpa: Optional[str]) -> Optional[str]:
    """Parse a GPA string and format to two decimal places.

    Only values in the 0.00–4.00 range are considered valid.

    Args:
        gpa: Raw GPA string like ``'3.95'`` or ``'4.0'``.

    Returns:
        A formatted string like ``'3.95'``, or ``None``.
    """
    if not gpa or not isinstance(gpa, str):
        return None
    match = re.search(r'(\d+\.?\d*)', gpa.strip())
    if match:
        val = float(match.group(1))
        if 0 <= val <= 4.0:
            return f"{val:.2f}"
    return None


def clean_status(status: Optional[str]) -> Optional[str]:
    """Normalize an admission status string.

    Maps common variations (e.g. "Accepted via Email", "Rejected
    on Portal") to one of three canonical labels.

    Args:
        status: Raw status text.

    Returns:
        ``'Accepted'``, ``'Rejected'``, ``'Waitlisted'``, or the
        original stripped string if no pattern matches.
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


def parse_date(date_str: Optional[str]) -> Optional[str]:
    """Convert a date string to ISO-8601 format (``YYYY-MM-DD``).

    Supports two formats commonly found in Grad Cafe data:
      - US format: ``MM/DD/YYYY``
      - ISO format: ``YYYY-MM-DD``

    Args:
        date_str: Raw date string.

    Returns:
        An ISO date string, or ``None`` on failure.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    date_str = date_str.strip()

    # Try US format first (MM/DD/YYYY)
    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if match:
        try:
            m, d, y = (int(x) for x in match.groups())
            return datetime(y, m, d).strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Try ISO format (YYYY-MM-DD)
    match = re.search(r'(\d{4})-(\d{1,2})-(\d{1,2})', date_str)
    if match:
        try:
            y, m, d = (int(x) for x in match.groups())
            return datetime(y, m, d).strftime('%Y-%m-%d')
        except ValueError:
            pass

    return None


def remove_html(text: Optional[str]) -> Optional[str]:
    """Strip HTML tags and decode the five most common HTML entities.

    Args:
        text: Raw text that may contain HTML markup.

    Returns:
        Cleaned plaintext, or ``None`` if the result is empty.
    """
    if not text:
        return None
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Decode common entities
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    # Collapse whitespace
    text = ' '.join(text.split()).strip()
    return text if text else None


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------

def save_cleaned_data(data: list[dict],
                      filename: str = 'applicant_data_cleaned.json') -> str:
    """Write cleaned data to a JSON file.

    Creates parent directories if they do not exist.

    Args:
        data: The cleaned applicant records.
        filename: Destination file path.

    Returns:
        The filename that was written.
    """
    directory = os.path.dirname(filename)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    with open(filename, 'w', encoding='utf-8') as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    return filename


def load_cleaned_data(filename: str = 'applicant_data_cleaned.json') -> list:
    """Load cleaned data from a JSON file.

    Args:
        filename: Path to the JSON file.

    Returns:
        Parsed list, or ``[]`` if the file does not exist.
    """
    if not os.path.exists(filename):
        return []
    with open(filename, 'r', encoding='utf-8') as fh:
        return json.load(fh)
