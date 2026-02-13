"""
Shared pytest fixtures for the Grad Cafe test suite.

Provides:
- A test PostgreSQL database (created automatically)
- Sample applicant records
- Flask test app and client with fake scraper/loader
- Database cleanup between tests
"""

import os
import pytest
import psycopg2

from src.app import create_app
from src.load_data import CREATE_TABLE_SQL


# ---------------------------------------------------------------------------
# Database URL helpers
# ---------------------------------------------------------------------------

# Default connects to a local Postgres; CI overrides via env-var.
_BASE_URL = os.environ.get(
    'TEST_DATABASE_URL',
    'postgresql://postgres:196301@localhost:5432/gradcafe_test'
)

# We also need a connection to the *default* database to create the test db.
_ADMIN_URL = os.environ.get(
    'ADMIN_DATABASE_URL',
    'postgresql://postgres:196301@localhost:5432/postgres'
)

TEST_DB_NAME = 'gradcafe_test'


# ---------------------------------------------------------------------------
# Sample data used across many tests
# ---------------------------------------------------------------------------

SAMPLE_RECORDS = [
    {
        'url': 'https://gradcafe.com/result/1001',
        'program': 'Computer Science, Massachusetts Institute of Technology',
        'status': 'Accepted',
        'term': 'Fall 2026',
        'degree': 'PhD',
        'gpa': 3.95,
        'gre': 170,
        'gre_v': 165,
        'gre_aw': 5.0,
        'comments': 'Great program!',
        'us_or_international': 'American',
        'llm_generated_program': 'Computer Science',
        'llm_generated_university': 'Massachusetts Institute of Technology',
    },
    {
        'url': 'https://gradcafe.com/result/1002',
        'program': 'Computer Science, Stanford University',
        'status': 'Accepted',
        'term': 'Fall 2026',
        'degree': 'PhD',
        'gpa': 3.80,
        'gre': 168,
        'gre_v': 162,
        'gre_aw': 4.5,
        'comments': None,
        'us_or_international': 'International',
        'llm_generated_program': 'Computer Science',
        'llm_generated_university': 'Stanford University',
    },
    {
        'url': 'https://gradcafe.com/result/1003',
        'program': 'Computer Science, Johns Hopkins University',
        'status': 'Accepted',
        'term': 'Fall 2026',
        'degree': 'Masters',
        'gpa': 3.70,
        'gre': None,
        'gre_v': None,
        'gre_aw': None,
        'comments': 'Happy to be accepted!',
        'us_or_international': 'American',
        'llm_generated_program': 'Computer Science',
        'llm_generated_university': 'Johns Hopkins University',
    },
    {
        'url': 'https://gradcafe.com/result/1004',
        'program': 'Physics, Stanford University',
        'status': 'Accepted',
        'term': 'Fall 2025',
        'degree': 'PhD',
        'gpa': 3.60,
        'gre': 165,
        'gre_v': 160,
        'gre_aw': 4.0,
        'comments': None,
        'us_or_international': 'International',
        'llm_generated_program': 'Physics',
        'llm_generated_university': 'Stanford University',
    },
    {
        'url': 'https://gradcafe.com/result/1005',
        'program': 'Biology, Harvard University',
        'status': 'Rejected',
        'term': 'Fall 2025',
        'degree': 'PhD',
        'gpa': 3.50,
        'gre': None,
        'gre_v': None,
        'gre_aw': None,
        'comments': 'Disappointing',
        'us_or_international': 'American',
        'llm_generated_program': 'Biology',
        'llm_generated_university': 'Harvard University',
    },
]


# ---------------------------------------------------------------------------
# Session-scoped: create the test database once
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session', autouse=True)
def _ensure_test_database():
    """Create the test database if it does not exist."""
    try:
        conn = psycopg2.connect(_ADMIN_URL)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (TEST_DB_NAME,)
        )
        if not cur.fetchone():
            cur.execute(f'CREATE DATABASE {TEST_DB_NAME}')
        cur.close()
        conn.close()
    except Exception:
        # If we cannot create, assume it already exists (CI).
        pass


# ---------------------------------------------------------------------------
# Function-scoped: fresh table for every test that uses `db_url`
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_url(_ensure_test_database):
    """Provide the test database URL and create a fresh table."""
    conn = psycopg2.connect(_BASE_URL)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS applicants")
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    cur.close()
    conn.close()
    return _BASE_URL


# ---------------------------------------------------------------------------
# Fake scraper / loader for Flask tests
# ---------------------------------------------------------------------------

def _fake_scraper():
    """Return canned sample records (no network)."""
    return list(SAMPLE_RECORDS)


def _fake_loader(records, database_url):
    """Insert records directly using plain SQL (test helper)."""
    conn = psycopg2.connect(database_url)
    cur = conn.cursor()
    for r in records:
        cur.execute(
            """
            INSERT INTO applicants
                (program, comments, url, status, term,
                 us_or_international, gpa, gre, gre_v, gre_aw,
                 degree, llm_generated_program,
                 llm_generated_university)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (url) DO NOTHING
            """,
            (
                r.get('program'), r.get('comments'), r.get('url'),
                r.get('status'), r.get('term'),
                r.get('us_or_international'),
                r.get('gpa'), r.get('gre'), r.get('gre_v'),
                r.get('gre_aw'), r.get('degree'),
                r.get('llm_generated_program'),
                r.get('llm_generated_university'),
            ),
        )
    conn.commit()
    cur.close()
    conn.close()


# ---------------------------------------------------------------------------
# Flask app & client fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def app(db_url):
    """Create a test Flask app wired to the test database."""
    application = create_app({
        'DATABASE_URL': db_url,
        'TESTING': True,
        'SCRAPER_FUNC': _fake_scraper,
        'LOADER_FUNC': _fake_loader,
    })
    return application


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def seeded_client(client):
    """Client with data already pulled into the test DB."""
    client.post('/pull_data')
    return client
