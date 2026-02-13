"""
test_db_insert.py - Database write and query tests.

Covers the load_data module (inserting records, idempotency) and
the query_data module (all nine queries plus two custom ones).

Author: Aaron Xu
"""

import pytest
import psycopg2

from tests.conftest import SAMPLE_RECORDS


# --- Inserts via /pull_data ---

@pytest.mark.db
def test_insert_rows_exist_after_pull(client, db_url):
    """After pulling, each sample record should be in the DB."""
    resp = client.post('/pull_data')
    assert resp.status_code == 200

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    assert count == len(SAMPLE_RECORDS)


@pytest.mark.db
def test_required_fields_not_null(client, db_url):
    """url, status, term, and degree should never be NULL."""
    client.post('/pull_data')

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute(
        "SELECT url, status, term, degree FROM applicants"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    for url, status, term, degree in rows:
        assert url is not None
        assert status is not None
        assert term is not None
        assert degree is not None


# --- Idempotency (UNIQUE constraint on url) ---

@pytest.mark.db
def test_duplicate_pull_no_duplicates(client, db_url):
    """Pulling the same data twice should not create duplicate rows."""
    client.post('/pull_data')
    client.post('/pull_data')

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    assert count == len(SAMPLE_RECORDS)


# --- Analysis query results ---

@pytest.mark.db
def test_run_analysis_queries_keys(client, db_url):
    """The result dict must contain every key the template uses."""
    client.post('/pull_data')

    from src.app import run_analysis_queries
    results = run_analysis_queries(db_url)

    expected_keys = [
        'q1_fall_2026_count', 'total_count',
        'international_count', 'american_count',
        'international_percentage',
        'avg_gpa', 'avg_gre', 'avg_gre_v', 'avg_gre_aw',
        'american_fall_2026_gpa',
        'fall_2025_total', 'fall_2025_accepted',
        'fall_2025_acceptance_rate',
        'fall_2026_acceptance_gpa',
        'jhu_masters_cs',
        'phd_cs_top_schools',
        'phd_cs_top_schools_llm',
        'top_programs',
        'acceptance_by_degree',
    ]
    for key in expected_keys:
        assert key in results, f"Missing key: {key}"


@pytest.mark.db
def test_analysis_values_correct(client, db_url):
    """Spot-check counts against our known sample data."""
    client.post('/pull_data')
    from src.app import run_analysis_queries
    r = run_analysis_queries(db_url)

    assert r['q1_fall_2026_count'] == 3   # 3 of our 5 records are Fall 2026
    assert r['total_count'] == 5
    assert r['international_count'] == 2
    assert r['american_count'] == 3


# --- load_data helper tests ---

@pytest.mark.db
def test_safe_float():
    """Quick check: valid floats, None, and non-numeric strings."""
    from src.load_data import safe_float
    assert safe_float(3.5) == 3.5
    assert safe_float('4.0') == 4.0
    assert safe_float(None) is None
    assert safe_float('abc') is None


@pytest.mark.db
def test_convert_international_status():
    """True/False/string inputs should map to the right labels."""
    from src.load_data import convert_international_status
    assert convert_international_status(True) == 'International'
    assert convert_international_status(False) == 'American'
    assert convert_international_status(None) == 'Other'
    assert convert_international_status('International') == 'International'
    assert convert_international_status('American') == 'American'
    assert convert_international_status('Unknown') == 'Unknown'


@pytest.mark.db
def test_prepare_row():
    """The returned tuple should have 14 elements (one per column)."""
    from src.load_data import prepare_row
    row = prepare_row(SAMPLE_RECORDS[0])
    assert isinstance(row, tuple)
    assert len(row) == 14


@pytest.mark.db
def test_prepare_row_no_us_field():
    """When us_or_international is absent, fall back to the 'international' flag."""
    from src.load_data import prepare_row
    entry = {
        'program': 'CS', 'university': 'MIT',
        'international': True, 'url': 'http://test',
    }
    row = prepare_row(entry)
    assert row[6] == 'International'  # us_or_international column


@pytest.mark.db
def test_insert_records(db_url):
    """insert_records should insert all rows and return the count."""
    from src.load_data import insert_records
    count = insert_records(SAMPLE_RECORDS, db_url)
    assert count == len(SAMPLE_RECORDS)


@pytest.mark.db
def test_create_table(db_url):
    """Calling create_table twice shouldn't raise (IF NOT EXISTS)."""
    from src.load_data import create_table
    create_table(db_url)   # should not raise
    create_table(db_url)   # second call also fine


@pytest.mark.db
def test_load_json_data_missing_file():
    """load_json_data returns [] for non-existent file."""
    from src.load_data import load_json_data
    assert load_json_data('/no/such/file.json') == []


@pytest.mark.db
def test_load_json_data_valid(tmp_path):
    """load_json_data reads a valid JSON file."""
    import json
    from src.load_data import load_json_data
    fp = tmp_path / 'data.json'
    fp.write_text(json.dumps([1, 2, 3]))
    assert load_json_data(str(fp)) == [1, 2, 3]


@pytest.mark.db
def test_get_database_url_default(monkeypatch):
    """load_data.get_database_url returns default when env unset."""
    from src.load_data import get_database_url
    monkeypatch.delenv('DATABASE_URL', raising=False)
    assert 'postgresql' in get_database_url()


@pytest.mark.db
def test_load_data_main(monkeypatch, capsys):
    """When there's no JSON file, main() should print 'No data'."""
    from src.load_data import main
    monkeypatch.setattr(
        'src.load_data.load_json_data', lambda p: []
    )
    main()
    assert 'No data' in capsys.readouterr().out


@pytest.mark.db
def test_load_data_main_with_data(monkeypatch, db_url):
    """When JSON data exists, main() should insert into the DB."""
    from src import load_data

    monkeypatch.setattr(
        load_data, 'load_json_data',
        lambda p: list(SAMPLE_RECORDS)
    )
    monkeypatch.setattr(
        load_data, 'get_database_url', lambda: db_url
    )
    load_data.main()

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants")
    assert cur.fetchone()[0] > 0
    cur.close()
    conn.close()


# --- query_data module ---

@pytest.mark.db
def test_query_data_run_all(client, db_url):
    """run_all_queries should return q1..q9 + custom_1 + custom_2."""
    client.post('/pull_data')
    from src.query_data import run_all_queries
    r = run_all_queries(db_url)
    for key in ('q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 'q8', 'q9',
                'custom_1', 'custom_2'):
        assert key in r


@pytest.mark.db
def test_query_data_individual_functions(client, db_url):
    """Smoke test: every single query function runs and returns something."""
    client.post('/pull_data')
    from src import query_data as qd
    assert isinstance(qd.query_fall_2026_count(db_url), int)
    assert 'percentage' in qd.query_international_percentage(db_url)
    assert 'avg_gpa' in qd.query_average_scores(db_url)
    qd.query_american_fall_2026_gpa(db_url)
    assert 'percentage' in qd.query_fall_2025_acceptance_rate(db_url)
    qd.query_fall_2026_acceptance_gpa(db_url)
    assert isinstance(qd.query_jhu_masters_cs(db_url), int)
    assert isinstance(qd.query_top_schools_phd_cs(db_url), int)
    assert isinstance(qd.query_top_schools_phd_cs_llm(db_url), int)
    assert isinstance(qd.query_top_programs(db_url), list)
    assert isinstance(qd.query_acceptance_by_degree(db_url), list)


@pytest.mark.db
def test_query_data_get_database_url(monkeypatch):
    """query_data.get_database_url reads from environment."""
    from src.query_data import get_database_url
    monkeypatch.delenv('DATABASE_URL', raising=False)
    assert 'postgresql' in get_database_url()


@pytest.mark.db
def test_query_data_get_connection(db_url):
    """query_data.get_connection returns a valid connection."""
    from src.query_data import get_connection
    conn = get_connection(db_url)
    assert conn is not None
    conn.close()


@pytest.mark.db
def test_query_data_main(monkeypatch, db_url, capsys):
    """main() should print the analysis banner to stdout."""
    from src import query_data as qd
    from tests.conftest import _fake_loader, _fake_scraper

    # Seed data first
    from src.load_data import create_table
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS applicants")
    from src.load_data import CREATE_TABLE_SQL
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    cur.close()
    conn.close()
    _fake_loader(_fake_scraper(), db_url)

    monkeypatch.setattr(qd, 'get_database_url', lambda: db_url)
    qd.main()
    out = capsys.readouterr().out
    assert 'GRAD CAFE DATA ANALYSIS' in out
