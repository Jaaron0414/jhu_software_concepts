"""SQL query functions for the Grad Cafe analysis.

Each public function runs one analytical query against the
``applicants`` table and returns a structured result.  All functions
accept an optional ``database_url`` parameter so the test suite can
redirect them to a dedicated test database.

Author: Jie Xu
Course: JHU Modern Software Concepts
Date: February 2026
"""

from __future__ import annotations

import os
from typing import Any, Optional

import psycopg2


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_database_url() -> str:
    """Return the PostgreSQL connection string.

    Reads ``DATABASE_URL`` from the environment; falls back to a
    local development default.

    Returns:
        A PostgreSQL connection string.
    """
    return os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:196301@localhost:5432/gradcafe'
    )


def get_connection(database_url: Optional[str] = None) -> psycopg2.extensions.connection:
    """Open a new psycopg2 connection.

    Args:
        database_url: Optional override.  Defaults to
            ``get_database_url()``.

    Returns:
        A live psycopg2 connection object.
    """
    url = database_url or get_database_url()
    return psycopg2.connect(url)


# ---------------------------------------------------------------------------
# Individual query functions (Q1 – Q9 + two custom)
# ---------------------------------------------------------------------------
# Each function opens its own connection for simplicity.
# TODO: refactor to share a single connection if performance matters.

def query_fall_2026_count(database_url: Optional[str] = None) -> int:
    """Q1: How many applicants applied for Fall 2026?

    Args:
        database_url: Optional Postgres connection string.

    Returns:
        An integer count.
    """
    conn = get_connection(database_url)
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026'"
    )
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


def query_international_percentage(database_url: Optional[str] = None) -> dict:
    """Q2: What percentage of entries are international students?

    Args:
        database_url: Optional Postgres connection string.

    Returns:
        A dict with keys ``total``, ``international``, ``american``,
        ``other``, and ``percentage``.
    """
    conn = get_connection(database_url)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM applicants")
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM applicants "
        "WHERE us_or_international = 'International'"
    )
    international = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM applicants "
        "WHERE us_or_international = 'American'"
    )
    american = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM applicants "
        "WHERE us_or_international = 'Other'"
    )
    other = cur.fetchone()[0]

    cur.close()
    conn.close()

    # Guard against division-by-zero when the table is empty
    percentage = round(
        (international / total) * 100, 2
    ) if total > 0 else 0.00

    return {
        'total': total,
        'international': international,
        'american': american,
        'other': other,
        'percentage': percentage,
    }


def query_average_scores(database_url: Optional[str] = None) -> dict:
    """Q3: Average GPA, GRE, GRE-V, and GRE-AW across all applicants.

    Only applicants who reported each score are included in the
    respective average (``WHERE ... IS NOT NULL``).

    Args:
        database_url: Optional Postgres connection string.

    Returns:
        A dict with keys ``avg_gpa``, ``avg_gre``, ``avg_gre_v``,
        and ``avg_gre_aw``.
    """
    conn = get_connection(database_url)
    cur = conn.cursor()

    cur.execute("SELECT AVG(gpa) FROM applicants WHERE gpa IS NOT NULL")
    avg_gpa = cur.fetchone()[0]

    cur.execute("SELECT AVG(gre) FROM applicants WHERE gre IS NOT NULL")
    avg_gre = cur.fetchone()[0]

    cur.execute("SELECT AVG(gre_v) FROM applicants WHERE gre_v IS NOT NULL")
    avg_gre_v = cur.fetchone()[0]

    cur.execute("SELECT AVG(gre_aw) FROM applicants WHERE gre_aw IS NOT NULL")
    avg_gre_aw = cur.fetchone()[0]

    cur.close()
    conn.close()

    return {
        'avg_gpa': avg_gpa,
        'avg_gre': avg_gre,
        'avg_gre_v': avg_gre_v,
        'avg_gre_aw': avg_gre_aw,
    }


def query_american_fall_2026_gpa(database_url: Optional[str] = None) -> Optional[float]:
    """Q4: Average GPA of American students applying for Fall 2026.

    Args:
        database_url: Optional Postgres connection string.

    Returns:
        The average GPA as a float, or ``None``.
    """
    conn = get_connection(database_url)
    cur = conn.cursor()
    cur.execute(
        "SELECT AVG(gpa) FROM applicants "
        "WHERE us_or_international = 'American' "
        "AND term = 'Fall 2026' AND gpa IS NOT NULL"
    )
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


def query_fall_2025_acceptance_rate(database_url: Optional[str] = None) -> dict:
    """Q5: What percentage of Fall 2025 entries are acceptances?

    Uses ``ILIKE '%%Accept%%'`` so that variations like "Accepted
    via Email" are counted.  Double-percent is required because
    psycopg2 treats ``%`` as a parameter marker.

    Args:
        database_url: Optional Postgres connection string.

    Returns:
        A dict with keys ``total``, ``accepted``, and ``percentage``.
    """
    conn = get_connection(database_url)
    cur = conn.cursor()

    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2025'"
    )
    total = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM applicants "
        "WHERE term = 'Fall 2025' AND status ILIKE '%%Accept%%'"
    )
    accepted = cur.fetchone()[0]

    cur.close()
    conn.close()

    percentage = round(
        (accepted / total) * 100, 2
    ) if total > 0 else 0.00

    return {
        'total': total,
        'accepted': accepted,
        'percentage': percentage,
    }


def query_fall_2026_acceptance_gpa(database_url: Optional[str] = None) -> Optional[float]:
    """Q6: Average GPA of accepted Fall 2026 applicants.

    Args:
        database_url: Optional Postgres connection string.

    Returns:
        The average GPA as a float, or ``None``.
    """
    conn = get_connection(database_url)
    cur = conn.cursor()
    cur.execute(
        "SELECT AVG(gpa) FROM applicants "
        "WHERE term = 'Fall 2026' AND status ILIKE '%%Accept%%' "
        "AND gpa IS NOT NULL"
    )
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


def query_jhu_masters_cs(database_url: Optional[str] = None) -> int:
    """Q7: How many applicants to JHU Masters in Computer Science?

    Matches both "Johns Hopkins" and "JHU" abbreviations via ILIKE.

    Args:
        database_url: Optional Postgres connection string.

    Returns:
        An integer count.
    """
    conn = get_connection(database_url)
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM applicants "
        "WHERE (program ILIKE '%%johns hopkins%%' "
        "OR program ILIKE '%%jhu%%') "
        "AND program ILIKE '%%computer science%%' "
        "AND degree ILIKE '%%master%%'"
    )
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


def query_top_schools_phd_cs(database_url: Optional[str] = None) -> int:
    """Q8: 2026 PhD CS acceptances at four top schools.

    Schools checked: Georgetown, MIT, Stanford, Carnegie Mellon.

    Args:
        database_url: Optional Postgres connection string.

    Returns:
        An integer count of matching acceptances.
    """
    conn = get_connection(database_url)
    cur = conn.cursor()
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
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


def query_top_schools_phd_cs_llm(database_url: Optional[str] = None) -> int:
    """Q9: Same as Q8 but using LLM-generated program/university fields.

    This lets us compare results between raw text matching (Q8) and
    the LLM-cleaned field matching (Q9).

    Args:
        database_url: Optional Postgres connection string.

    Returns:
        An integer count.
    """
    conn = get_connection(database_url)
    cur = conn.cursor()
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
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


def query_top_programs(database_url: Optional[str] = None) -> list[tuple]:
    """Custom Q1: Top 10 most popular programs by applicant count.

    Args:
        database_url: Optional Postgres connection string.

    Returns:
        A list of ``(program_name, count)`` tuples.
    """
    conn = get_connection(database_url)
    cur = conn.cursor()
    cur.execute(
        "SELECT llm_generated_program, COUNT(*) AS cnt "
        "FROM applicants WHERE llm_generated_program IS NOT NULL "
        "GROUP BY llm_generated_program ORDER BY cnt DESC LIMIT 10"
    )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


def query_acceptance_by_degree(database_url: Optional[str] = None) -> list[tuple]:
    """Custom Q2: Acceptance rate broken down by degree type.

    Args:
        database_url: Optional Postgres connection string.

    Returns:
        A list of ``(degree, total, accepted, rate)`` tuples.
    """
    conn = get_connection(database_url)
    cur = conn.cursor()
    cur.execute(
        "SELECT degree, COUNT(*) AS total, "
        "SUM(CASE WHEN status ILIKE '%%Accept%%' THEN 1 ELSE 0 END) "
        "AS accepted, "
        "ROUND(100.0 * SUM(CASE WHEN status ILIKE '%%Accept%%' "
        "THEN 1 ELSE 0 END) / COUNT(*), 2) AS rate "
        "FROM applicants WHERE degree IS NOT NULL "
        "GROUP BY degree ORDER BY total DESC"
    )
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


# ---------------------------------------------------------------------------
# Aggregate runner
# ---------------------------------------------------------------------------

def run_all_queries(database_url: Optional[str] = None) -> dict[str, Any]:
    """Run every query and return a consolidated results dict.

    Args:
        database_url: Optional Postgres connection string.

    Returns:
        A dict with keys ``q1`` through ``q9``, ``custom_1``,
        and ``custom_2``.
    """
    return {
        'q1': query_fall_2026_count(database_url),
        'q2': query_international_percentage(database_url),
        'q3': query_average_scores(database_url),
        'q4': query_american_fall_2026_gpa(database_url),
        'q5': query_fall_2025_acceptance_rate(database_url),
        'q6': query_fall_2026_acceptance_gpa(database_url),
        'q7': query_jhu_masters_cs(database_url),
        'q8': query_top_schools_phd_cs(database_url),
        'q9': query_top_schools_phd_cs_llm(database_url),
        'custom_1': query_top_programs(database_url),
        'custom_2': query_acceptance_by_degree(database_url),
    }


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """Print all analysis results to the terminal."""
    results = run_all_queries()
    print("=" * 60)
    print("GRAD CAFE DATA ANALYSIS")
    print("=" * 60)

    print(f"\nQ1: Fall 2026 count: {results['q1']}")

    q2 = results['q2']
    print(f"\nQ2: International: {q2['percentage']}%")

    q3 = results['q3']
    print(f"\nQ3: Avg GPA={q3['avg_gpa']}  GRE={q3['avg_gre']}  "
          f"GRE_V={q3['avg_gre_v']}  GRE_AW={q3['avg_gre_aw']}")

    print(f"\nQ4: American F26 GPA: {results['q4']}")

    q5 = results['q5']
    print(f"\nQ5: F25 acceptance: {q5['percentage']}%")

    print(f"\nQ6: F26 acceptance GPA: {results['q6']}")
    print(f"\nQ7: JHU Masters CS: {results['q7']}")
    print(f"\nQ8: Top schools PhD CS: {results['q8']}")
    print(f"\nQ9: LLM fields: {results['q9']}")

    print(f"\nCustom Q1: Top programs: {results['custom_1']}")
    print(f"\nCustom Q2: Acceptance by degree: {results['custom_2']}")

    print("=" * 60)
    return results


if __name__ == '__main__':  # pragma: no cover
    main()
