# Module 4 — Testing & Documentation

**Author:** Aaron Xu  
**Course:** JHU Modern Software Concepts (Spring 2026)

## What this is

This module adds a full **pytest** test suite and **Sphinx** documentation on
top of the Grad Cafe analytics app from Module 3.  The test suite covers all
source files in `src/` at 100% line coverage.

## Project layout

```
module_4/
  src/
    app.py            # Flask web app (factory pattern)
    scrape.py         # Grad Cafe scraper (urllib + BeautifulSoup)
    clean.py          # Data cleaning / normalization
    load_data.py      # Bulk-insert into PostgreSQL
    query_data.py     # Nine required queries + two custom
    templates/
      index.html      # Dashboard page
  tests/
    conftest.py       # Shared fixtures (test DB, sample records)
    test_*.py         # One file per concern (see markers below)
  docs/               # Sphinx .rst source files
  pytest.ini          # Markers, coverage config
  requirements.txt
```

## Getting started

```bash
cd module_4
python -m venv .venv
.venv\Scripts\activate       # or source .venv/bin/activate on Mac/Linux
pip install -r requirements.txt

# Start the Flask app
python -m src.app            # http://localhost:5000

# Run tests (needs a local Postgres)
pytest
```

## Environment variables

- `DATABASE_URL` — Postgres connection string (defaults to `postgresql://postgres:196301@localhost:5432/gradcafe`)
- `TEST_DATABASE_URL` — same, but for the test database (defaults to `gradcafe_test`)

## Pytest markers

| Marker        | What it covers                                |
|---------------|-----------------------------------------------|
| `web`         | Flask routes, page rendering, scraper/cleaner |
| `buttons`     | POST endpoints and busy-state gating          |
| `analysis`    | "Answer:" labels, decimal formatting          |
| `db`          | Inserts, idempotency, query functions         |
| `integration` | End-to-end pull -> update -> render           |

```bash
# run just one category
pytest -m db
```

## Documentation

Published on Read the Docs: **https://jhu-software-concepts-jiexu.readthedocs.io/en/latest/**

To build locally:

```bash
cd docs
sphinx-build -b html . _build/html
# open _build/html/index.html
```

## Acknowledgments

Completed with assistance from Cursor (Claude), Gemini, and GitHub Copilot.
