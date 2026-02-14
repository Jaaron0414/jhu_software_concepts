"""Load applicant data into PostgreSQL.

Creates the ``applicants`` table (if it does not exist), converts JSON
records into row tuples, and bulk-inserts them using ``execute_values``.
The ``url`` column carries a UNIQUE constraint so that re-pulling the
same data never creates duplicate rows (``ON CONFLICT DO NOTHING``).

Author: Jie Xu
Course: JHU Modern Software Concepts
Date: February 2026
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import psycopg2
from psycopg2.extras import execute_values

# ---------------------------------------------------------------------------
# SQL: table schema with a UNIQUE constraint on ``url`` for idempotency
# ---------------------------------------------------------------------------

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS applicants (
    p_id SERIAL PRIMARY KEY,
    program TEXT,
    comments TEXT,
    date_added DATE,
    url TEXT UNIQUE,
    status TEXT,
    term TEXT,
    us_or_international TEXT,
    gpa FLOAT,
    gre FLOAT,
    gre_v FLOAT,
    gre_aw FLOAT,
    degree TEXT,
    llm_generated_program TEXT,
    llm_generated_university TEXT
);
"""


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_database_url() -> str:
    """Return the PostgreSQL connection string.

    Reads ``DATABASE_URL`` from the environment; falls back to a
    sensible local-development default.

    Returns:
        A PostgreSQL connection string.
    """
    return os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:196301@localhost:5432/gradcafe'
    )


def create_table(database_url: Optional[str] = None) -> None:
    """Run ``CREATE TABLE IF NOT EXISTS`` for the applicants table.

    Args:
        database_url: Optional override for the connection string.
    """
    url = database_url or get_database_url()
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    cur.close()
    conn.close()


# ---------------------------------------------------------------------------
# Row-preparation helpers
# ---------------------------------------------------------------------------

def safe_float(value: Any) -> Optional[float]:
    """Safely convert *value* to a float.

    Args:
        value: Any input (string, number, or ``None``).

    Returns:
        The float value, or ``None`` if conversion fails.
    """
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def convert_international_status(value: Any) -> str:
    """Map a raw nationality indicator to a standard label.

    The scraper stores ``True``/``False`` booleans, while cleaned data
    may already contain ``'International'`` or ``'American'`` strings.

    Args:
        value: Boolean, string, or ``None``.

    Returns:
        One of ``'International'``, ``'American'``, ``'Other'``, or
        the original string if it doesn't match known patterns.
    """
    if value is None:
        return 'Other'
    if value is True or str(value) == 'International':
        return 'International'
    if value is False or str(value) == 'American':
        return 'American'
    return str(value)


def prepare_row(entry: dict) -> tuple:
    """Convert one applicant dict into a tuple matching the INSERT columns.

    Handles both raw-scraper dicts (which have ``'university'`` and
    ``'entry_link'``) and cleaned/pre-processed dicts (which may
    already have ``'url'`` and ``'term'``).

    Args:
        entry: A single applicant dict.

    Returns:
        A 14-element tuple aligned with the INSERT column order.
    """
    university = entry.get('university', '') or ''
    program = entry.get('program', '') or ''
    combined = f"{program}, {university}".strip(', ')

    # Prefer the explicit field; fall back to the boolean ``international`` flag
    us_or_intl = entry.get('us_or_international')
    if us_or_intl is None:
        us_or_intl = convert_international_status(
            entry.get('international')
        )

    return (
        combined or None,                                    # program
        entry.get('comments'),                               # comments
        None,                                                # date_added
        entry.get('url') or entry.get('entry_link'),         # url (UNIQUE)
        entry.get('status'),                                 # status
        entry.get('semester_year') or entry.get('term'),     # term
        us_or_intl,                                          # us_or_international
        safe_float(entry.get('gpa')),                        # gpa
        safe_float(
            entry.get('gre_quantitative') or entry.get('gre')
        ),                                                   # gre
        safe_float(
            entry.get('gre_verbal') or entry.get('gre_v')
        ),                                                   # gre_v
        safe_float(entry.get('gre_aw')),                     # gre_aw
        entry.get('degree'),                                 # degree
        entry.get('llm_generated_program'),
        entry.get('llm_generated_university'),
    )


# ---------------------------------------------------------------------------
# Bulk insert
# ---------------------------------------------------------------------------

def insert_records(records: list[dict],
                   database_url: Optional[str] = None) -> int:
    """Bulk-insert applicant records, skipping duplicates.

    Uses ``ON CONFLICT (url) DO NOTHING`` so that re-pulling the
    same data is safe (idempotent).

    Args:
        records: List of applicant dicts to insert.
        database_url: Optional Postgres connection string override.

    Returns:
        The number of rows passed to ``execute_values`` (not
        necessarily the number actually inserted, due to conflicts).
    """
    url = database_url or get_database_url()
    conn = psycopg2.connect(url)
    cur = conn.cursor()

    rows = [prepare_row(r) for r in records]

    insert_sql = """
        INSERT INTO applicants (
            program, comments, date_added, url, status, term,
            us_or_international, gpa, gre, gre_v, gre_aw, degree,
            llm_generated_program, llm_generated_university
        ) VALUES %s
        ON CONFLICT (url) DO NOTHING
    """

    execute_values(cur, insert_sql, rows, page_size=1000)
    conn.commit()
    cur.close()
    conn.close()
    return len(rows)


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def load_json_data(filepath: str) -> list:
    """Load and return data from a JSON file.

    Args:
        filepath: Path to the JSON file.

    Returns:
        Parsed JSON data, or an empty list if the file is missing.
    """
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Load the Module 2 JSON data file into PostgreSQL."""
    json_path = os.path.join(
        os.path.dirname(__file__), '..', '..',
        'module_2', 'llm_extend_applicant_data.json'
    )
    data = load_json_data(json_path)
    if not data:
        print("No data to load.")
        return

    database_url = get_database_url()
    create_table(database_url)
    count = insert_records(data, database_url)
    print(f"Inserted {count} rows.")


if __name__ == '__main__':  # pragma: no cover
    main()
