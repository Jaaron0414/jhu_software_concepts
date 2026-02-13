"""
test_flask_page.py - Tests for the Flask app factory and the main page.

Makes sure create_app works, all routes are registered, and
that GET / renders the expected HTML (buttons, labels, etc.).

Author: Aaron Xu
"""

import pytest
from bs4 import BeautifulSoup
from src.app import create_app, get_database_url, get_db_connection, main


# --- App factory and configuration ---

@pytest.mark.web
def test_create_app_returns_flask_instance(db_url):
    """Sanity check: create_app gives us an actual Flask object."""
    app = create_app({'DATABASE_URL': db_url, 'TESTING': True})
    assert app is not None
    assert hasattr(app, 'test_client')


@pytest.mark.web
def test_app_has_required_routes(app):
    """All four routes should be registered."""
    rules = [r.rule for r in app.url_map.iter_rules()]
    assert '/' in rules
    assert '/pull_data' in rules
    assert '/update_analysis' in rules
    assert '/status' in rules


@pytest.mark.web
def test_custom_config_applied(db_url):
    """Extra config keys we pass in should show up on app.config."""
    app = create_app({
        'DATABASE_URL': db_url,
        'TESTING': True,
        'MY_KEY': 42,
    })
    assert app.config['MY_KEY'] == 42


# --- Page rendering (GET /) ---

@pytest.mark.web
def test_index_returns_200(client):
    """Basic smoke test for the main page."""
    resp = client.get('/')
    assert resp.status_code == 200


@pytest.mark.web
def test_page_contains_analysis_text(client):
    """The word 'Analysis' should appear somewhere on the page."""
    html = client.get('/').data.decode()
    assert 'Analysis' in html


@pytest.mark.web
def test_page_contains_answer_label(seeded_client):
    """After seeding data, the rendered page should have 'Answer:' labels."""
    html = seeded_client.get('/').data.decode()
    assert 'Answer:' in html


@pytest.mark.web
def test_page_has_pull_data_button(client):
    """Pull Data button must have data-testid='pull-data-btn'."""
    soup = BeautifulSoup(client.get('/').data, 'html.parser')
    btn = soup.find(attrs={'data-testid': 'pull-data-btn'})
    assert btn is not None
    assert 'Pull Data' in btn.get_text()


@pytest.mark.web
def test_page_has_update_analysis_button(client):
    """Update Analysis button must have data-testid='update-analysis-btn'."""
    soup = BeautifulSoup(client.get('/').data, 'html.parser')
    btn = soup.find(attrs={'data-testid': 'update-analysis-btn'})
    assert btn is not None
    assert 'Update Analysis' in btn.get_text()


# --- Helper function tests ---

@pytest.mark.web
def test_get_database_url_default(monkeypatch):
    """With no env var, we should still get a valid Postgres URL."""
    monkeypatch.delenv('DATABASE_URL', raising=False)
    url = get_database_url()
    assert 'postgresql' in url


@pytest.mark.web
def test_get_database_url_from_env(monkeypatch):
    """When DATABASE_URL is set, that value should be used."""
    monkeypatch.setenv('DATABASE_URL', 'postgresql://test:test@host/db')
    url = get_database_url()
    assert url == 'postgresql://test:test@host/db'


@pytest.mark.web
def test_get_db_connection(db_url):
    """Make sure we can actually open a connection to the test DB."""
    conn = get_db_connection(db_url)
    assert conn is not None
    conn.close()


@pytest.mark.web
def test_index_handles_db_error(db_url):
    """If the DB is unreachable, index should still render (empty results)."""
    app = create_app({
        'DATABASE_URL': 'postgresql://bad:bad@localhost:9999/nope',
        'TESTING': True,
    })
    resp = app.test_client().get('/')
    assert resp.status_code == 200


# --- main() entry point ---

@pytest.mark.web
def test_main_calls_run(monkeypatch):
    """main() should create the app and call .run(port=5000)."""
    called = {}

    class FakeApp:
        def run(self, **kw):
            called['run'] = kw

    monkeypatch.setattr('src.app.create_app', lambda: FakeApp())
    main()
    assert 'run' in called
    assert called['run']['port'] == 5000


# --- Default scraper / loader wrappers ---

@pytest.mark.web
def test_default_scraper_executes(monkeypatch):
    """_default_scraper should delegate to scrape.scrape_data."""
    from src.app import _default_scraper
    monkeypatch.setattr(
        'src.scrape.scrape_data',
        lambda **kw: [{'fake': True}]
    )
    result = _default_scraper()
    assert result == [{'fake': True}]


@pytest.mark.web
def test_default_loader_executes(monkeypatch):
    """_default_loader should delegate to load_data.insert_records."""
    from src.app import _default_loader
    called = {}
    monkeypatch.setattr(
        'src.load_data.insert_records',
        lambda recs, url: called.update(n=len(recs))
    )
    _default_loader([1, 2], 'postgresql://x')
    assert called['n'] == 2


# --- Threading branch (production mode) ---

@pytest.mark.web
def test_pull_data_uses_thread_when_not_testing(db_url):
    """In production mode (TESTING=False), pull runs in a background thread."""
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
