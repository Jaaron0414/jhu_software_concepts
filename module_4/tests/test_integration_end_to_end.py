"""
test_integration_end_to_end.py - Full-flow integration tests.

These tests exercise the whole pipeline: pull -> DB -> update -> render,
to make sure all the pieces work together.

Author: Aaron Xu
"""

import re
import pytest
import psycopg2
from bs4 import BeautifulSoup

from tests.conftest import SAMPLE_RECORDS


@pytest.mark.integration
def test_end_to_end_pull_update_render(client, db_url):
    """Full pipeline: pull data, update analysis, check the page."""
    # 1) Pull data into the DB
    resp = client.post('/pull_data')
    assert resp.status_code == 200
    assert resp.get_json()['ok'] is True

    # 2) Verify rows actually landed in the DB
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants")
    assert cur.fetchone()[0] == len(SAMPLE_RECORDS)
    cur.close()
    conn.close()

    # 3) Update analysis
    resp = client.post('/update_analysis')
    assert resp.status_code == 200
    assert resp.get_json()['ok'] is True

    # 4) Render the page and sanity-check the output
    html = client.get('/').data.decode()
    assert 'Answer:' in html
    assert 'Analysis' in html

    # Every percentage must have exactly two decimal places
    for pct in re.findall(r'(\d+\.\d+)%', html):
        assert len(pct.split('.')[1]) == 2


@pytest.mark.integration
def test_end_to_end_page_shows_correct_count(client, db_url):
    """Q1 answer should be 3 (we have three Fall 2026 entries)."""
    client.post('/pull_data')
    soup = BeautifulSoup(client.get('/').data, 'html.parser')
    answers = soup.find_all('div', class_='answer')

    q1_text = answers[0].get_text()
    assert '3' in q1_text


@pytest.mark.integration
def test_multiple_pulls_no_duplicates(client, db_url):
    """Pulling twice shouldn't create duplicate rows (UNIQUE on url)."""
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
    """After a synchronous pull (TESTING=True), we should be idle again."""
    client.post('/pull_data')
    resp = client.get('/status')
    assert resp.get_json()['is_running'] is False
