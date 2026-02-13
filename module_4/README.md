# Module 4 — Pytest & Sphinx

JHU Modern Software Concepts — Testing and Documentation Assignment

## Overview

This module adds a comprehensive **pytest test suite** and **Sphinx documentation** to the Grad Cafe analytics application built in Module 3.

## Directory Structure

```
module_4/
  src/                   # Application code
    app.py               # Flask web application (create_app factory)
    scrape.py            # Grad Cafe web scraper
    clean.py             # Data cleaning utilities
    load_data.py         # PostgreSQL data loader
    query_data.py        # SQL query functions
    templates/
      index.html         # Analysis dashboard template
  tests/                 # Pytest test suite
    conftest.py          # Shared fixtures
    test_flask_page.py   # Flask route & page rendering tests
    test_buttons.py      # Button endpoint & busy-state tests
    test_analysis_format.py  # Answer labels & percentage formatting
    test_db_insert.py    # Database insert, idempotency, queries
    test_integration_end_to_end.py  # End-to-end flow tests
    test_scrape.py       # Scraper module tests
    test_clean.py        # Cleaning module tests
  docs/                  # Sphinx documentation source
  pytest.ini             # Pytest config (markers, coverage)
  requirements.txt       # Python dependencies
  README.md              # This file
```

## Quick Start

```bash
cd module_4
python -m venv .venv
.venv\Scripts\activate         # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt

# Run the app
python -m src.app
# Visit http://localhost:5000

# Run the tests
pytest
```

## Environment Variables

| Variable           | Default                                                     |
|--------------------|-------------------------------------------------------------|
| `DATABASE_URL`     | `postgresql://postgres:196301@localhost:5432/gradcafe`       |
| `TEST_DATABASE_URL`| `postgresql://postgres:196301@localhost:5432/gradcafe_test`  |

## Test Markers

| Marker        | Scope                                        |
|---------------|----------------------------------------------|
| `web`         | Flask routes, page rendering, HTML structure  |
| `buttons`     | Pull Data / Update Analysis button endpoints  |
| `analysis`    | Answer labels, percentage formatting          |
| `db`          | Database schema, inserts, selects             |
| `integration` | End-to-end pull → update → render flows       |

Run all tests:

```bash
pytest -m "web or buttons or analysis or db or integration"
```

## Documentation

Sphinx docs are located in `docs/`. To build:

```bash
cd docs
sphinx-build -b html . _build/html
```

## References

This module was completed with the help of AI tools: Cursor (Claude 4), Gemini 3.0, and GitHub Copilot.
