"""
query_data.py - SQL queries for the Grad Cafe analysis.

Each function runs one query and returns its result.  They all accept
an optional database_url so the test suite can point them at a
separate test database.

Author: Aaron Xu
Course: JHU Modern Software Concepts
Date: February 2026
"""

import os
import psycopg2


def get_database_url():
    """Read DATABASE_URL from the environment, fall back to local default."""
    return os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:196301@localhost:5432/gradcafe'
    )


def get_connection(database_url=None):
    """Open a psycopg2 connection to the given (or default) database."""
    url = database_url or get_database_url()
    return psycopg2.connect(url)


# ---- Individual query functions ----
# Each opens its own connection for simplicity.
# TODO: refactor to share a connection if performance matters.

def query_fall_2026_count(database_url=None):
    """Q1: How many entries applied for Fall 2026?"""
    conn = get_connection(database_url)
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026'"
    )
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


def query_international_percentage(database_url=None):
    """Q2: What percentage of entries are international?"""
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


def query_average_scores(database_url=None):
    """Q3: Average GPA, GRE, GRE V, GRE AW for applicants who report them."""
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


def query_american_fall_2026_gpa(database_url=None):
    """Q4: Average GPA of American students in Fall 2026."""
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


def query_fall_2025_acceptance_rate(database_url=None):
    """Q5: What percent of Fall 2025 entries are acceptances?"""
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


def query_fall_2026_acceptance_gpa(database_url=None):
    """Q6: Average GPA of accepted Fall 2026 applicants."""
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


def query_jhu_masters_cs(database_url=None):
    """Q7: How many applicants to JHU Masters in Computer Science?"""
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


def query_top_schools_phd_cs(database_url=None):
    """Q8: 2026 PhD CS acceptances at Georgetown/MIT/Stanford/CMU."""
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


def query_top_schools_phd_cs_llm(database_url=None):
    """Q9: Same as Q8 using LLM-generated fields."""
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


def query_top_programs(database_url=None):
    """Custom Q1: Top 10 most popular programs."""
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


def query_acceptance_by_degree(database_url=None):
    """Custom Q2: Acceptance rate by degree type."""
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


def run_all_queries(database_url=None):
    """Convenience wrapper — runs all queries and returns a single dict."""
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


def main():
    """Print all query results to the terminal."""
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
