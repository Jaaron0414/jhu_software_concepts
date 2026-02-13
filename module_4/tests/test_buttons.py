"""
test_buttons.py - Button & Busy-State Behaviour Tests

Verifies:
  - POST /pull_data returns 200 with {"ok": true} when idle
  - POST /update_analysis returns 200 when idle
  - Both endpoints return 409 with {"busy": true} when busy
"""

import pytest


# ---------- POST /pull_data ----------

@pytest.mark.buttons
def test_pull_data_returns_200_when_idle(client):
    """POST /pull_data returns 200 when not busy."""
    resp = client.post('/pull_data')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['ok'] is True


@pytest.mark.buttons
def test_pull_data_triggers_loader(client, db_url):
    """After POST /pull_data, rows exist in the database."""
    import psycopg2
    client.post('/pull_data')
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    assert count > 0


# ---------- POST /update_analysis ----------

@pytest.mark.buttons
def test_update_analysis_returns_200_when_idle(client):
    """POST /update_analysis returns 200 when not busy."""
    resp = client.post('/update_analysis')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['ok'] is True


# ---------- busy gating ----------

@pytest.mark.buttons
def test_pull_data_returns_409_when_busy(app, client):
    """POST /pull_data returns 409 when a pull is already in progress."""
    app.config['_busy'] = True
    resp = client.post('/pull_data')
    assert resp.status_code == 409
    body = resp.get_json()
    assert body['busy'] is True
    assert body['ok'] is False
    app.config['_busy'] = False     # cleanup


@pytest.mark.buttons
def test_update_analysis_returns_409_when_busy(app, client):
    """POST /update_analysis returns 409 when busy."""
    app.config['_busy'] = True
    resp = client.post('/update_analysis')
    assert resp.status_code == 409
    body = resp.get_json()
    assert body['busy'] is True
    app.config['_busy'] = False


# ---------- /status endpoint ----------

@pytest.mark.buttons
def test_status_returns_not_running(client):
    """GET /status reports is_running=false when idle."""
    resp = client.get('/status')
    assert resp.status_code == 200
    assert resp.get_json()['is_running'] is False


@pytest.mark.buttons
def test_status_returns_running_when_busy(app, client):
    """GET /status reports is_running=true when busy."""
    app.config['_busy'] = True
    resp = client.get('/status')
    assert resp.get_json()['is_running'] is True
    app.config['_busy'] = False
