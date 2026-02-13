"""
load_data.py - Load applicant data into PostgreSQL.

Creates the applicants table, converts JSON records into rows,
and bulk-inserts them.  The url column has a UNIQUE constraint so
that re-pulling the same data won't create duplicates.

Author: Jie Xu
Course: JHU Modern Software Concepts
Date: February 2026
"""

import json
import os

import psycopg2
from psycopg2.extras import execute_values


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
    """Read DATABASE_URL from the environment, fall back to local default."""
    return os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:196301@localhost:5432/gradcafe'
    )


def create_table(database_url=None):
    """Run CREATE TABLE IF NOT EXISTS for the applicants table."""
    url = database_url or get_database_url()
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    cur.close()
    conn.close()


def safe_float(value):
    """Try to convert value to float; return None if it fails."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def convert_international_status(value):
    """Map True/False/'International'/'American' to a consistent label."""
    if value is None:
        return 'Other'
    if value is True or str(value) == 'International':
        return 'International'
    if value is False or str(value) == 'American':
        return 'American'
    return str(value)


def prepare_row(entry):
    """Convert one applicant dict into a tuple for the INSERT statement."""
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
    """Bulk-insert records, skipping any whose url already exists."""
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
    """Load JSON from filepath; returns [] if the file doesn't exist."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def main():
    """CLI entry point — load the Module 2 JSON into Postgres."""
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
