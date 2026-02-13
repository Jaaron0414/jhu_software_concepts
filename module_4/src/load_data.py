"""
load_data.py - Load applicant data into PostgreSQL

Provides functions to create the applicants table,
prepare rows from JSON records, and bulk-insert them.

Author: Student
Date: February 2026
"""

import json
import os

import psycopg2
from psycopg2.extras import execute_values


# SQL to create the applicants table with a UNIQUE constraint on url
# so duplicate pulls do not create duplicate rows.
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


def get_database_url():
    """Return DATABASE_URL from environment or default.

    Returns:
        str: PostgreSQL connection string.
    """
    return os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:196301@localhost:5432/gradcafe'
    )


def create_table(database_url=None):
    """Create the applicants table if it does not exist.

    Args:
        database_url: Optional connection string override.
    """
    url = database_url or get_database_url()
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    cur.close()
    conn.close()


def safe_float(value):
    """Safely convert *value* to float, returning None on failure.

    Args:
        value: Any value to convert.

    Returns:
        float or None.
    """
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def convert_international_status(value):
    """Convert a boolean or string to a text nationality label.

    Args:
        value: True/False, 'International'/'American', or None.

    Returns:
        One of 'International', 'American', or 'Other'.
    """
    if value is None:
        return 'Other'
    if value is True or str(value) == 'International':
        return 'International'
    if value is False or str(value) == 'American':
        return 'American'
    return str(value)


def prepare_row(entry):
    """Convert one applicant dict into a tuple matching the INSERT columns.

    Args:
        entry: dict with raw applicant data.

    Returns:
        tuple of values for one database row.
    """
    university = entry.get('university', '') or ''
    program = entry.get('program', '') or ''
    combined = f"{program}, {university}".strip(', ')

    # Determine the nationality field
    us_or_intl = entry.get('us_or_international')
    if us_or_intl is None:
        us_or_intl = convert_international_status(
            entry.get('international')
        )

    return (
        combined or None,                                    # program
        entry.get('comments'),                               # comments
        None,                                                # date_added
        entry.get('url') or entry.get('entry_link'),         # url
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


def insert_records(records, database_url=None):
    """Insert applicant records into PostgreSQL, skipping duplicates.

    Uses ON CONFLICT (url) DO NOTHING to enforce idempotency.

    Args:
        records: List of applicant dicts.
        database_url: Optional connection string override.

    Returns:
        int: Number of rows passed to execute_values.
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


def load_json_data(filepath):
    """Load and return JSON data from *filepath*.

    Args:
        filepath: Path to a JSON file.

    Returns:
        list: Parsed JSON data, or empty list if file missing.
    """
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def main():
    """Load data from the Module 2 JSON file into PostgreSQL."""
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
