"""
app.py - Flask Web Application for Grad Cafe Data Analysis

Provides a web interface to view graduate school admissions analysis.
Supports pulling new data and refreshing analysis results.

Routes:
    GET  /                  - Main analysis page
    POST /pull_data         - Start data pull (scraping + loading)
    POST /update_analysis   - Refresh analysis results
    GET  /status            - Check if a pull is in progress

Author: Student
Date: February 2026
"""

import os
import threading

import psycopg2
from flask import Flask, render_template, jsonify


def get_database_url():
    """Return the DATABASE_URL from environment or a sensible default.

    Returns:
        str: PostgreSQL connection string.
    """
    return os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:196301@localhost:5432/gradcafe'
    )


def get_db_connection(database_url=None):
    """Create and return a new database connection.

    Args:
        database_url: Optional connection string override.

    Returns:
        psycopg2 connection object.
    """
    url = database_url or get_database_url()
    return psycopg2.connect(url)


def run_analysis_queries(database_url=None):
    """Execute all analysis queries and return a results dictionary.

    The dictionary keys match the template variables used in index.html.

    Args:
        database_url: Optional connection string override.

    Returns:
        dict: Analysis results with keys like q1_fall_2026_count, etc.
    """
    results = {}
    conn = get_db_connection(database_url)
    cur = conn.cursor()

    try:
        # Q1: Fall 2026 count
        cur.execute(
            "SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026'"
        )
        results['q1_fall_2026_count'] = cur.fetchone()[0]

        # Q2: International percentage
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

        if total > 0:
            results['international_percentage'] = round(
                (results['international_count'] / total) * 100, 2
            )
        else:
            results['international_percentage'] = 0.00

        # Q3: Average scores
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

        # Q4: American Fall 2026 GPA
        cur.execute(
            "SELECT AVG(gpa) FROM applicants "
            "WHERE us_or_international = 'American' "
            "AND term = 'Fall 2026' AND gpa IS NOT NULL"
        )
        results['american_fall_2026_gpa'] = cur.fetchone()[0] or 0

        # Q5: Fall 2025 acceptance rate
        cur.execute(
            "SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2025'"
        )
        f25_total = cur.fetchone()[0]
        results['fall_2025_total'] = f25_total

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

        # Q6: Fall 2026 acceptance GPA
        cur.execute(
            "SELECT AVG(gpa) FROM applicants "
            "WHERE term = 'Fall 2026' AND status ILIKE '%%Accept%%' "
            "AND gpa IS NOT NULL"
        )
        results['fall_2026_acceptance_gpa'] = cur.fetchone()[0] or 0

        # Q7: JHU Masters CS
        cur.execute(
            "SELECT COUNT(*) FROM applicants "
            "WHERE (program ILIKE '%%johns hopkins%%' "
            "OR program ILIKE '%%jhu%%') "
            "AND program ILIKE '%%computer science%%' "
            "AND degree ILIKE '%%master%%'"
        )
        results['jhu_masters_cs'] = cur.fetchone()[0]

        # Q8: Top schools PhD CS 2026
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

        # Q9: Using LLM fields
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

        # Custom Q1: Top 10 programs
        cur.execute(
            "SELECT llm_generated_program, COUNT(*) AS cnt "
            "FROM applicants WHERE llm_generated_program IS NOT NULL "
            "GROUP BY llm_generated_program ORDER BY cnt DESC LIMIT 10"
        )
        results['top_programs'] = cur.fetchall()

        # Custom Q2: Acceptance rate by degree
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
        cur.close()
        conn.close()

    return results


def _default_scraper():
    """Default scraper — imports and runs the scrape module.

    Returns:
        list: Raw applicant records from Grad Cafe.
    """
    from src.scrape import scrape_data
    return scrape_data(result_type='all', num_pages=10, delay=0.5)


def _default_loader(records, database_url):
    """Default loader — imports and runs the load_data module.

    Args:
        records: List of applicant dicts.
        database_url: PostgreSQL connection string.
    """
    from src.load_data import insert_records
    insert_records(records, database_url)


def create_app(config=None):
    """Flask application factory.

    Args:
        config: Optional dict with configuration overrides.
            DATABASE_URL   - PostgreSQL connection string
            SCRAPER_FUNC   - callable() -> list of dicts
            LOADER_FUNC    - callable(records, database_url)
            TESTING        - run pull synchronously when True

    Returns:
        Configured Flask application instance.
    """
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), 'templates')
    )

    # Defaults
    app.config['DATABASE_URL'] = get_database_url()
    app.config['SCRAPER_FUNC'] = _default_scraper
    app.config['LOADER_FUNC'] = _default_loader
    app.config['_busy'] = False

    if config:
        app.config.update(config)

    # ------------------------------------------------------------------
    # Routes
    # ------------------------------------------------------------------
    @app.route('/')
    def index():
        """Render the main analysis page."""
        try:
            results = run_analysis_queries(app.config['DATABASE_URL'])
        except Exception:
            results = {}
        return render_template('index.html', results=results)

    @app.route('/pull_data', methods=['POST'])
    def pull_data():
        """Start a data pull.  Returns 409 if already busy."""
        if app.config['_busy']:
            return jsonify({'ok': False, 'busy': True}), 409

        app.config['_busy'] = True
        scraper_fn = app.config['SCRAPER_FUNC']
        loader_fn = app.config['LOADER_FUNC']
        db_url = app.config['DATABASE_URL']

        def _run_pull():
            try:
                records = scraper_fn()
                loader_fn(records, db_url)
            finally:
                app.config['_busy'] = False

        if app.config.get('TESTING'):
            # Synchronous in test mode so assertions work immediately
            _run_pull()
        else:
            thread = threading.Thread(target=_run_pull)
            thread.daemon = True
            thread.start()

        return jsonify({'ok': True}), 200

    @app.route('/update_analysis', methods=['POST'])
    def update_analysis():
        """Refresh analysis results.  Returns 409 if busy."""
        if app.config['_busy']:
            return jsonify({'ok': False, 'busy': True}), 409
        return jsonify({'ok': True}), 200

    @app.route('/status')
    def status():
        """Return current busy status as JSON."""
        return jsonify({'is_running': app.config['_busy']})

    return app


def main():
    """Run the Flask development server."""
    application = create_app()
    application.run(debug=True, port=5000)


if __name__ == '__main__':  # pragma: no cover
    main()
