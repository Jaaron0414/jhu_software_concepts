# Module 3 - Database Queries Assignment

JHU Modern Software Concepts

## Overview

This module loads the Grad Cafe applicant data (from Module 2) into a PostgreSQL database and runs SQL queries to analyze graduate school admissions patterns.

## Files

- `load_data.py` - Loads JSON data into PostgreSQL
- `query_data.py` - Contains SQL queries to answer assignment questions
- `app.py` - Flask web app to display results
- `scrape.py` - Web scraper (copied from Module 2)
- `clean.py` - Data cleaning utilities
- `limitations.txt` - Essay on data limitations

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. PostgreSQL Setup

Make sure PostgreSQL is installed and running. Create a database named `gradcafe`:

```sql
CREATE DATABASE gradcafe;
```

### 3. Load Data

```bash
python load_data.py
```

This loads the data from `../module_2/llm_extend_applicant_data.json` into the database.

### 4. Run Queries

```bash
python query_data.py
```

This prints answers to all 9 required questions plus 2 custom questions.

### 5. Run Web App

```bash
python app.py
```

Then open http://localhost:5000 in your browser.

## Web App Features

- **Pull Data**: Scrapes new entries from Grad Cafe
- **Update Analysis**: Refreshes the statistics display

## Assignment Questions Answered

1. Fall 2026 applicant count
2. International student percentage
3. Average GPA, GRE, GRE V, GRE AW
4. American students Fall 2026 average GPA
5. Fall 2025 acceptance percentage
6. Fall 2026 acceptances average GPA
7. JHU Masters CS count
8. Top schools PhD CS 2026 acceptances
9. Same as Q8 using LLM fields

Plus 2 custom questions:
- Top 10 most popular programs
- Acceptance rate by degree type
