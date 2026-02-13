"""
test_flask_page.py - Flask App & Page Rendering Tests

Verifies:
  - App factory creates a testable Flask app with required routes
  - GET / returns 200 with required page components
  - Page contains both buttons, "Analysis" text, "Answer:" labels
"""

import pytest
from bs4 import BeautifulSoup
from src.app import create_app, get_database_url, get_db_connection, main


# ---------- app factory / config ----------

@pytest.mark.web
def test_create_app_returns_flask_instance(db_url):
    """create_app() returns a Flask app object."""
    app = create_app({'DATABASE_URL': db_url, 'TESTING': True})
    assert app is not None
    assert hasattr(app, 'test_client')


@pytest.mark.web
def test_app_has_required_routes(app):
    """The app registers /, /pull_data, /update_analysis, /status."""
    rules = [r.rule for r in app.url_map.iter_rules()]
    assert '/' in rules
    assert '/pull_data' in rules
    assert '/update_analysis' in rules
    assert '/status' in rules


@pytest.mark.web
def test_custom_config_applied(db_url):
    """Config dict passed to create_app is honoured."""
    app = create_app({
        'DATABASE_URL': db_url,
        'TESTING': True,
        'MY_KEY': 42,
    })
    assert app.config['MY_KEY'] == 42


# ---------- GET / (page load) ----------

@pytest.mark.web
def test_index_returns_200(client):
    """GET / responds with 200."""
    resp = client.get('/')
    assert resp.status_code == 200


@pytest.mark.web
def test_page_contains_analysis_text(client):
    """Page text includes 'Analysis'."""
    html = client.get('/').data.decode()
    assert 'Analysis' in html


@pytest.mark.web
def test_page_contains_answer_label(seeded_client):
    """Page includes at least one 'Answer:' label."""
    html = seeded_client.get('/').data.decode()
    assert 'Answer:' in html


@pytest.mark.web
def test_page_has_pull_data_button(client):
    """Page contains a Pull Data button with data-testid."""
    soup = BeautifulSoup(client.get('/').data, 'html.parser')
    btn = soup.find(attrs={'data-testid': 'pull-data-btn'})
    assert btn is not None
    assert 'Pull Data' in btn.get_text()


@pytest.mark.web
def test_page_has_update_analysis_button(client):
    """Page contains an Update Analysis button with data-testid."""
    soup = BeautifulSoup(client.get('/').data, 'html.parser')
    btn = soup.find(attrs={'data-testid': 'update-analysis-btn'})
    assert btn is not None
    assert 'Update Analysis' in btn.get_text()


# ---------- helper functions ----------

@pytest.mark.web
def test_get_database_url_default(monkeypatch):
    """get_database_url returns a default when DATABASE_URL is unset."""
    monkeypatch.delenv('DATABASE_URL', raising=False)
    url = get_database_url()
    assert 'postgresql' in url


@pytest.mark.web
def test_get_database_url_from_env(monkeypatch):
    """get_database_url reads DATABASE_URL from environment."""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://test:test@host/db')
    url = get_database_url()
    assert url == 'postgresql://test:test@host/db'


@pytest.mark.web
def test_get_db_connection(db_url):
    """get_db_connection opens a live connection."""
    conn = get_db_connection(db_url)
    assert conn is not None
    conn.close()


@pytest.mark.web
def test_index_handles_db_error(db_url):
    """If analysis queries fail, GET / still returns 200 with empty results."""
    app = create_app({
        'DATABASE_URL': 'postgresql://bad:bad@localhost:9999/nope',
        'TESTING': True,
    })
    resp = app.test_client().get('/')
    assert resp.status_code == 200


# ---------- main() ----------

@pytest.mark.web
def test_main_calls_run(monkeypatch):
    """main() creates an app and calls app.run()."""
    called = {}

    class FakeApp:
        def run(self, **kw):
            called['run'] = kw

    monkeypatch.setattr('src.app.create_app', lambda: FakeApp())
    main()
    assert 'run' in called
    assert called['run']['port'] == 5000


# ---------- default scraper/loader references ----------

@pytest.mark.web
def test_default_scraper_executes(monkeypatch):
    """_default_scraper calls scrape.scrape_data and returns its result."""
    from src.app import _default_scraper
    monkeypatch.setattr(
        'src.scrape.scrape_data',
        lambda **kw: [{'fake': True}]
    )
    result = _default_scraper()
    assert result == [{'fake': True}]


@pytest.mark.web
def test_default_loader_executes(monkeypatch):
    """_default_loader calls load_data.insert_records."""
    from src.app import _default_loader
    called = {}
    monkeypatch.setattr(
        'src.load_data.insert_records',
        lambda recs, url: called.update(n=len(recs))
    )
    _default_loader([1, 2], 'postgresql://x')
    assert called['n'] == 2


# ---------- threading branch (non-TESTING) ----------

@pytest.mark.web
def test_pull_data_uses_thread_when_not_testing(db_url):
    """When TESTING is False, pull_data spawns a background thread."""
    import time
    from tests.conftest import _fake_scraper, _fake_loader

    app = create_app({
        'DATABASE_URL': db_url,
        'TESTING': False,
        'SCRAPER_FUNC': _fake_scraper,
        'LOADER_FUNC': _fake_loader,
    })
    client = app.test_client()
    resp = client.post('/pull_data')
    assert resp.status_code == 200
    # Wait briefly for the background thread
    time.sleep(1)
    assert app.config['_busy'] is False
