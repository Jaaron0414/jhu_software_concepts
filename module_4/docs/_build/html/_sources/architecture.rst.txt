Architecture
============

The system has three layers:

Web Layer (Flask)
-----------------
``src/app.py`` exposes a single-page Flask application with four routes:

* ``GET /`` — renders the analysis dashboard (``templates/index.html``).
* ``POST /pull_data`` — triggers a background scrape + load cycle.
* ``POST /update_analysis`` — refreshes on-screen results (no-op when busy).
* ``GET /status`` — JSON health-check for the busy flag.

A ``create_app(config)`` factory makes the application fully testable:
callers can inject a fake scraper and loader to avoid network and
long-running operations during tests.

ETL Layer (Scrape + Clean)
--------------------------
``src/scrape.py``
    Uses ``urllib`` and ``BeautifulSoup`` to crawl Grad Cafe list pages,
    extracting university, program, degree, GPA, GRE scores, status,
    and comments.

``src/clean.py``
    Normalises raw data — standardises GPA/GRE values, converts dates
    to ISO-8601, strips HTML entities, and unifies status labels.

Database Layer (PostgreSQL)
---------------------------
``src/load_data.py``
    Creates the ``applicants`` table (with a ``UNIQUE`` constraint on
    ``url`` for idempotency) and bulk-inserts rows using
    ``psycopg2.extras.execute_values``.

``src/query_data.py``
    Contains individual SQL query functions (Q1–Q9 plus two custom
    queries) and a ``run_all_queries()`` aggregator that the Flask
    route calls at render time.

Busy-State Policy
-----------------
Only one pull may run at a time.  The ``_busy`` flag is set to ``True``
at the start of ``/pull_data`` and cleared in a ``finally`` block.
While busy, both ``/pull_data`` and ``/update_analysis`` return
**HTTP 409** with ``{"busy": true}``.

Idempotency Strategy
--------------------
The ``url`` column carries a ``UNIQUE`` constraint.  Inserts use
``ON CONFLICT (url) DO NOTHING``, so re-pulling the same data never
creates duplicate rows.
