Testing Guide
=============

Running the Full Suite
----------------------

.. code-block:: bash

   cd module_4
   pytest

``pytest.ini`` is pre-configured with ``--cov=src --cov-fail-under=100``,
so the command above also produces a coverage report and fails if any
source line is uncovered.

Pytest Markers
--------------

Every test carries at least one marker.  You can run subsets:

* ``web`` — Flask page load, route registration, HTML
* ``buttons`` — Pull Data / Update Analysis endpoints
* ``analysis`` — Answer labels, percentage formatting
* ``db`` — Database writes, queries, idempotency
* ``integration`` — End-to-end pull, update, render

.. code-block:: bash

   pytest -m web                     # page tests only
   pytest -m "db or integration"     # database-heavy tests
   pytest -m "web or buttons or analysis or db or integration"  # all

Stable Selectors
----------------

UI tests locate buttons via ``data-testid`` attributes:

* ``data-testid="pull-data-btn"`` — the Pull Data button
* ``data-testid="update-analysis-btn"`` — the Update Analysis button

Test Doubles & Fixtures
-----------------------

``conftest.py`` provides:

``app`` / ``client``
    A Flask app wired to a **test** PostgreSQL database with a fake
    (in-memory) scraper and loader injected via ``create_app(config)``.

``db_url``
    The test database URL.  The ``applicants`` table is recreated
    before every test that requests this fixture.

``seeded_client``
    A ``client`` that has already executed ``POST /pull_data`` so
    the database contains sample rows.

``_fake_scraper`` / ``_fake_loader``
    Return canned ``SAMPLE_RECORDS`` and insert them directly — no
    network, no file I/O.

Troubleshooting
---------------

**psycopg2 not found**
    ``pip install psycopg2-binary`` (ensure you are in the correct venv).

**Cannot create test database**
    Make sure PostgreSQL is running and the ``postgres`` user can
    create databases.  Alternatively, create ``gradcafe_test`` manually
    and set ``TEST_DATABASE_URL``.

**CI hangs on DB tests**
    Verify the ``services: postgres`` block in ``.github/workflows/tests.yml``
    and check that ``TEST_DATABASE_URL`` is exported.
