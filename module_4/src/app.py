"""Flask web application for Grad Cafe data analysis.

This module serves the analysis dashboard where users can pull new
data from thegradcafe.com and view aggregate statistics.  It uses
the ``create_app`` factory pattern so that tests can inject fake
scraper/loader functions without hitting the network.

Routes:
    GET  /                 - analysis dashboard
    POST /pull_data        - kick off a background scrape + load
    POST /update_analysis  - refresh results (blocked when busy)
    GET  /status           - JSON busy-flag for frontend polling

Author: Jie Xu
Course: JHU Modern Software Concepts
Date: February 2026
"""

from __future__ import annotations

import os
import threading
from typing import Any, Callable, Optional

import psycopg2
from flask import Flask, render_template, jsonify


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
# NOTE: ``get_database_url`` is duplicated in load_data.py and query_data.py.
# A shared config module would be cleaner, but keeping it simple for now.

def get_database_url() -> str:
    """Return the PostgreSQL connection string.

    Reads ``DATABASE_URL`` from the environment; falls back to a
    local development default so the app works out of the box.

    Returns:
        The PostgreSQL connection string.
    """
    return os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:196301@localhost:5432/gradcafe'
    )


def get_db_connection(database_url: Optional[str] = None) -> psycopg2.extensions.connection:
    """Open a new psycopg2 connection.

    Args:
        database_url: Optional override for the connection string.
            When ``None``, ``get_database_url()`` is used.

    Returns:
        A live psycopg2 connection object.
    """
    url = database_url or get_database_url()
    return psycopg2.connect(url)


# ---------------------------------------------------------------------------
# Analysis queries (all nine required + two custom)
# ---------------------------------------------------------------------------

def run_analysis_queries(database_url: Optional[str] = None) -> dict[str, Any]:
    """Execute all analysis queries and return template-ready results.

    The returned dict keys correspond exactly to the Jinja variables
    used in ``templates/index.html`` (e.g. ``q1_fall_2026_count``).

    Args:
        database_url: Optional Postgres connection string override.

    Returns:
        A dictionary of analysis results.  Empty dict on DB error.
    """
    results: dict[str, Any] = {}
    conn = get_db_connection(database_url)
    cur = conn.cursor()

    try:
        # Q1 — How many applicants applied for Fall 2026?
        cur.execute(
            "SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026'"
        )
        results['q1_fall_2026_count'] = cur.fetchone()[0]

        # Q2 — What percentage of entries are international students?
        cur.execute("SELECT COUNT(*) FROM applicants")
        total = cur.fetchone()[0]
        results['total_count'] = total

        cur.execute(
            "SELECT COUNT(*) FROM applicants "
            "WHERE us_or_international = 'International'"
        )
        results['international_count'] = cur.fetchone()[0]

        cur.execute(
            "SELECT COUNT(*) FROM applicants "
            "WHERE us_or_international = 'American'"
        )
        results['american_count'] = cur.fetchone()[0]

        # Percentage needs a guard against division-by-zero
        if total > 0:
            results['international_percentage'] = round(
                (results['international_count'] / total) * 100, 2
            )
        else:
            results['international_percentage'] = 0.00

        # Q3 — Average GPA, GRE, GRE-V, GRE-AW
        cur.execute(
            "SELECT AVG(gpa) FROM applicants WHERE gpa IS NOT NULL"
        )
        results['avg_gpa'] = cur.fetchone()[0] or 0

        cur.execute(
            "SELECT AVG(gre) FROM applicants WHERE gre IS NOT NULL"
        )
        results['avg_gre'] = cur.fetchone()[0] or 0

        cur.execute(
            "SELECT AVG(gre_v) FROM applicants WHERE gre_v IS NOT NULL"
        )
        results['avg_gre_v'] = cur.fetchone()[0] or 0

        cur.execute(
            "SELECT AVG(gre_aw) FROM applicants WHERE gre_aw IS NOT NULL"
        )
        results['avg_gre_aw'] = cur.fetchone()[0] or 0

        # Q4 — Average GPA of American students in Fall 2026
        cur.execute(
            "SELECT AVG(gpa) FROM applicants "
            "WHERE us_or_international = 'American' "
            "AND term = 'Fall 2026' AND gpa IS NOT NULL"
        )
        results['american_fall_2026_gpa'] = cur.fetchone()[0] or 0

        # Q5 — Fall 2025 acceptance rate
        cur.execute(
            "SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2025'"
        )
        f25_total = cur.fetchone()[0]
        results['fall_2025_total'] = f25_total

        # Using ILIKE '%%Accept%%' so it matches "Accepted", "Accepted via Email", etc.
        # Double-%% is required because psycopg2 treats a single % as a parameter marker.
        cur.execute(
            "SELECT COUNT(*) FROM applicants "
            "WHERE term = 'Fall 2025' AND status ILIKE '%%Accept%%'"
        )
        f25_accepted = cur.fetchone()[0]
        results['fall_2025_accepted'] = f25_accepted

        if f25_total > 0:
            results['fall_2025_acceptance_rate'] = round(
                (f25_accepted / f25_total) * 100, 2
            )
        else:
            results['fall_2025_acceptance_rate'] = 0.00

        # Q6 — Average GPA of accepted Fall 2026 applicants
        cur.execute(
            "SELECT AVG(gpa) FROM applicants "
            "WHERE term = 'Fall 2026' AND status ILIKE '%%Accept%%' "
            "AND gpa IS NOT NULL"
        )
        results['fall_2026_acceptance_gpa'] = cur.fetchone()[0] or 0

        # Q7 — How many applicants to JHU Masters in Computer Science?
        cur.execute(
            "SELECT COUNT(*) FROM applicants "
            "WHERE (program ILIKE '%%johns hopkins%%' "
            "OR program ILIKE '%%jhu%%') "
            "AND program ILIKE '%%computer science%%' "
            "AND degree ILIKE '%%master%%'"
        )
        results['jhu_masters_cs'] = cur.fetchone()[0]

        # Q8 — 2026 PhD CS acceptances at Georgetown / MIT / Stanford / CMU
        cur.execute(
            "SELECT COUNT(*) FROM applicants "
            "WHERE term ILIKE '%%2026%%' "
            "AND status ILIKE '%%Accept%%' "
            "AND degree ILIKE '%%PhD%%' "
            "AND program ILIKE '%%computer science%%' "
            "AND (program ILIKE '%%georgetown%%' "
            "OR program ILIKE '%%mit%%' "
            "OR program ILIKE '%%stanford%%' "
            "OR program ILIKE '%%carnegie mellon%%')"
        )
        results['phd_cs_top_schools'] = cur.fetchone()[0]

        # Q9 — Same as Q8 but using LLM-generated fields for comparison
        cur.execute(
            "SELECT COUNT(*) FROM applicants "
            "WHERE term ILIKE '%%2026%%' "
            "AND status ILIKE '%%Accept%%' "
            "AND degree ILIKE '%%PhD%%' "
            "AND llm_generated_program ILIKE '%%computer science%%' "
            "AND (llm_generated_university ILIKE '%%georgetown%%' "
            "OR llm_generated_university ILIKE '%%mit%%' "
            "OR llm_generated_university ILIKE '%%stanford%%' "
            "OR llm_generated_university ILIKE '%%carnegie mellon%%')"
        )
        results['phd_cs_top_schools_llm'] = cur.fetchone()[0]

        # Custom Q1 — Top 10 most popular programs (by LLM-cleaned name)
        cur.execute(
            "SELECT llm_generated_program, COUNT(*) AS cnt "
            "FROM applicants WHERE llm_generated_program IS NOT NULL "
            "GROUP BY llm_generated_program ORDER BY cnt DESC LIMIT 10"
        )
        results['top_programs'] = cur.fetchall()

        # Custom Q2 — Acceptance rate broken down by degree type
        cur.execute(
            "SELECT degree, COUNT(*) AS total, "
            "SUM(CASE WHEN status ILIKE '%%Accept%%' THEN 1 ELSE 0 END) "
            "AS accepted, "
            "ROUND(100.0 * SUM(CASE WHEN status ILIKE '%%Accept%%' "
            "THEN 1 ELSE 0 END) / COUNT(*), 2) AS rate "
            "FROM applicants WHERE degree IS NOT NULL "
            "GROUP BY degree ORDER BY total DESC"
        )
        results['acceptance_by_degree'] = cur.fetchall()

    finally:
        # Always close the cursor and connection, even if a query fails
        cur.close()
        conn.close()

    return results


# ---------------------------------------------------------------------------
# Default scraper / loader (imported lazily to avoid circular imports)
# ---------------------------------------------------------------------------

def _default_scraper() -> list[dict]:
    """Import ``src.scrape`` and pull ~10 pages of results.

    Returns:
        A list of raw applicant dicts from Grad Cafe.
    """
    from src.scrape import scrape_data
    return scrape_data(result_type='all', num_pages=10, delay=0.5)


def _default_loader(records: list[dict], database_url: str) -> None:
    """Import ``src.load_data`` and bulk-insert the given records.

    Args:
        records: List of applicant dicts to insert.
        database_url: PostgreSQL connection string.
    """
    from src.load_data import insert_records
    insert_records(records, database_url)


# ---------------------------------------------------------------------------
# Flask application factory
# ---------------------------------------------------------------------------

def create_app(config: Optional[dict] = None) -> Flask:
    """Create and configure the Flask application.

    Uses the *factory pattern* so that tests can inject overrides
    (e.g. a fake scraper, a test database URL, or ``TESTING=True``
    for synchronous data pulls).

    Args:
        config: Optional dict of configuration overrides.  Recognised
            keys include ``DATABASE_URL``, ``SCRAPER_FUNC``,
            ``LOADER_FUNC``, and ``TESTING``.

    Returns:
        A fully configured Flask application instance.
    """
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates')
    )

    # Sensible defaults — overridden by ``config`` dict if provided
    app.config['DATABASE_URL'] = get_database_url()
    app.config['SCRAPER_FUNC'] = _default_scraper
    app.config['LOADER_FUNC'] = _default_loader
    app.config['_busy'] = False  # busy flag prevents concurrent pulls

    if config:
        app.config.update(config)

    # --- Route definitions ---

    @app.route('/')
    def index():
        """Render the main analysis dashboard.

        If the database is unreachable (e.g. first run before any data
        is loaded), the page still renders with empty results.
        """
        try:
            results = run_analysis_queries(app.config['DATABASE_URL'])
        except Exception:
            # DB might not be set up yet — show the page anyway
            results = {}
        return render_template('index.html', results=results)

    @app.route('/pull_data', methods=['POST'])
    def pull_data():
        """Start a data-pull cycle (scrape + load).

        Returns:
            200 with ``{"ok": true}`` when the pull starts.
            409 with ``{"busy": true}`` if a pull is already running.
        """
        if app.config['_busy']:
            return jsonify({'ok': False, 'busy': True}), 409

        app.config['_busy'] = True
        scraper_fn: Callable = app.config['SCRAPER_FUNC']
        loader_fn: Callable = app.config['LOADER_FUNC']
        db_url: str = app.config['DATABASE_URL']

        def _run_pull() -> None:
            """Inner helper — runs scraper then loader; clears busy flag."""
            try:
                records = scraper_fn()
                loader_fn(records, db_url)
            finally:
                app.config['_busy'] = False

        if app.config.get('TESTING'):
            # In test mode, run synchronously so assertions work immediately
            _run_pull()
        else:
            # In production, run in a background thread to avoid blocking
            thread = threading.Thread(target=_run_pull)
            thread.daemon = True
            thread.start()

        return jsonify({'ok': True}), 200

    @app.route('/update_analysis', methods=['POST'])
    def update_analysis():
        """Refresh the analysis page.

        Returns:
            200 with ``{"ok": true}`` on success.
            409 with ``{"busy": true}`` if a pull is in progress.
        """
        if app.config['_busy']:
            return jsonify({'ok': False, 'busy': True}), 409
        return jsonify({'ok': True}), 200

    @app.route('/status')
    def status():
        """Return the current busy state as JSON.

        The frontend uses this endpoint to poll whether a pull is
        still in progress.
        """
        return jsonify({'is_running': app.config['_busy']})

    return app


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Start the Flask development server on port 5000."""
    application = create_app()
    application.run(debug=True, port=5000)


if __name__ == '__main__':  # pragma: no cover
    main()
