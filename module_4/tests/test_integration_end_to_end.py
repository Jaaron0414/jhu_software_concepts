"""
test_integration_end_to_end.py - Integration / End-to-End Tests

Verifies:
  - Full flow: pull -> update -> render shows correct data
  - Multiple pulls with overlapping data remain consistent
"""

import re
import pytest
import psycopg2
from bs4 import BeautifulSoup

from tests.conftest import SAMPLE_RECORDS


# ---------- end-to-end: pull -> update -> render ----------

@pytest.mark.integration
def test_end_to_end_pull_update_render(client, db_url):
    """Pull data, update analysis, then verify rendered page."""
    # Step 1: pull data
    resp = client.post('/pull_data')
    assert resp.status_code == 200
    assert resp.get_json()['ok'] is True

    # Step 2: verify rows in DB
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants")
    assert cur.fetchone()[0] == len(SAMPLE_RECORDS)
    cur.close()
    conn.close()

    # Step 3: update analysis (not busy, should succeed)
    resp = client.post('/update_analysis')
    assert resp.status_code == 200
    assert resp.get_json()['ok'] is True

    # Step 4: render page and check values
    html = client.get('/').data.decode()
    assert 'Answer:' in html
    assert 'Analysis' in html

    # Check percentages have two decimals
    for pct in re.findall(r'(\d+\.\d+)%', html):
        assert len(pct.split('.')[1]) == 2


@pytest.mark.integration
def test_end_to_end_page_shows_correct_count(client, db_url):
    """After pull + render, page shows correct Fall 2026 count."""
    client.post('/pull_data')
    soup = BeautifulSoup(client.get('/').data, 'html.parser')
    answers = soup.find_all('div', class_='answer')

    # Q1 answer should contain '3' (three Fall 2026 entries)
    q1_text = answers[0].get_text()
    assert '3' in q1_text


# ---------- multiple pulls ----------

@pytest.mark.integration
def test_multiple_pulls_no_duplicates(client, db_url):
    """Running POST /pull_data twice keeps row count consistent."""
    client.post('/pull_data')
    client.post('/pull_data')

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()

    assert count == len(SAMPLE_RECORDS)


@pytest.mark.integration
def test_status_idle_after_pull(client):
    """After synchronous pull, status reports not running."""
    client.post('/pull_data')
    resp = client.get('/status')
    assert resp.get_json()['is_running'] is False
