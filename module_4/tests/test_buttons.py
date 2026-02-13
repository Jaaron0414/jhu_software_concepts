"""
test_buttons.py - Tests for the Pull Data and Update Analysis buttons.

Checks that the two POST endpoints return the right status codes
and JSON payloads, and that the busy-state gating (409) works.

Author: Aaron Xu
"""

import pytest


# --- Pull Data button ---

@pytest.mark.buttons
def test_pull_data_returns_200_when_idle(client):
    """Normal case: pull_data should return 200 + ok=True."""
    resp = client.post('/pull_data')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['ok'] is True


@pytest.mark.buttons
def test_pull_data_triggers_loader(client, db_url):
    """After pulling, there should be rows in the applicants table."""
    import psycopg2
    client.post('/pull_data')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    assert count > 0


# --- Update Analysis button ---

@pytest.mark.buttons
def test_update_analysis_returns_200_when_idle(client):
    """update_analysis should return 200 + ok=True normally."""
    resp = client.post('/update_analysis')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['ok'] is True


# --- Busy-state gating (409 responses) ---

@pytest.mark.buttons
def test_pull_data_returns_409_when_busy(app, client):
    """If a pull is already running, we should get 409 + busy=True."""
    app.config['_busy'] = True
    try:
        resp = client.post('/pull_data')
        assert resp.status_code == 409
        body = resp.get_json()
        assert body['busy'] is True
        assert body['ok'] is False
    finally:
        app.config['_busy'] = False


@pytest.mark.buttons
def test_update_analysis_returns_409_when_busy(app, client):
    """Same idea — update_analysis is also blocked while busy."""
    app.config['_busy'] = True
    try:
        resp = client.post('/update_analysis')
        assert resp.status_code == 409
        body = resp.get_json()
        assert body['busy'] is True
    finally:
        app.config['_busy'] = False


# --- Status endpoint ---

@pytest.mark.buttons
def test_status_returns_not_running(client):
    """When nothing is happening, /status should say is_running=false."""
    resp = client.get('/status')
    assert resp.status_code == 200
    assert resp.get_json()['is_running'] is False


@pytest.mark.buttons
def test_status_returns_running_when_busy(app, client):
    """If we manually set _busy, /status should report it."""
    app.config['_busy'] = True
    try:
        resp = client.get('/status')
        assert resp.get_json()['is_running'] is True
    finally:
        app.config['_busy'] = False
