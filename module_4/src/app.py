"""
app.py - Flask web application for Grad Cafe data analysis.

This is the main web server that shows the analysis dashboard.
Users can pull new data from Grad Cafe and refresh results.

Routes:
    GET  /                 - analysis dashboard
    POST /pull_data        - kick off a background scrape + load
    POST /update_analysis  - refresh results (no-op when busy)
    GET  /status           - JSON busy check for frontend polling

Author: Jie Xu
Course: JHU Modern Software Concepts
Date: February 2026
"""

import os
import threading

import psycopg2
from flask import Flask, render_template, jsonify

# NOTE: get_database_url is duplicated in load_data.py and query_data.py.
# Ideally we'd have a shared config module, but keeping it simple for now.


def get_database_url():
    """Read DATABASE_URL from the environment, fall back to local default."""
    return os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:196301@localhost:5432/gradcafe'
    )


def get_db_connection(database_url=None):
    """Open a psycopg2 connection to the given (or default) database."""
    url = database_url or get_database_url()
    return psycopg2.connect(url)


def run_analysis_queries(database_url=None):
    """Run all nine required queries plus two custom ones.

    Returns a dict whose keys line up with the Jinja template variables
    in index.html.  If database_url is None we use the environment default.
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
    """Import the scrape module and pull ~10 pages of results."""
    from src.scrape import scrape_data
    return scrape_data(result_type='all', num_pages=10, delay=0.5)


def _default_loader(records, database_url):
    """Import load_data and bulk-insert the records."""
    from src.load_data import insert_records
    insert_records(records, database_url)


def create_app(config=None):
    """Application factory — creates and configures the Flask app.

    Pass a config dict to override DATABASE_URL, SCRAPER_FUNC,
    LOADER_FUNC, or TESTING (synchronous pull for test assertions).
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

    # --- Routes ---

    @app.route('/')
    def index():
        """Main page — runs all queries and renders the dashboard."""
        try:
            results = run_analysis_queries(app.config['DATABASE_URL'])
        except Exception:
            # If the DB isn't set up yet, just show empty results
            results = {}
        return render_template('index.html', results=results)

    @app.route('/pull_data', methods=['POST'])
    def pull_data():
        """Kick off a data pull. Returns 409 if one is already running."""
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
        """Re-render analysis. Returns 409 when a pull is in progress."""
        if app.config['_busy']:
            return jsonify({'ok': False, 'busy': True}), 409
        return jsonify({'ok': True}), 200

    @app.route('/status')
    def status():
        """Simple JSON endpoint so the frontend can poll busy state."""
        return jsonify({'is_running': app.config['_busy']})

    return app


def main():
    """Start the dev server on port 5000."""
    application = create_app()
    application.run(debug=True, port=5000)


if __name__ == '__main__':  # pragma: no cover
    main()
