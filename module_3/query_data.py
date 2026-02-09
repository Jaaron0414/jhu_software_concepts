"""
query_data.py - Module 3 Assignment
JHU Modern Software Concepts

This script runs SQL queries on the Grad Cafe database to answer
the assignment questions about graduate school admissions data.

Author: Student
Date: February 2026
"""

import psycopg2

# Database connection settings
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'gradcafe'
DB_USER = 'postgres'
DB_PASSWORD = '196301'


def get_connection():
    """Creates and returns a database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


# ============================================================
# Question 1: How many entries applied for Fall 2026?
# ============================================================
def query_1_fall_2026_count():
    """
    Counts entries who applied for Fall 2026.
    
    Query: SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026'
    
    Why: Simple COUNT with WHERE clause to filter by term.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026'")
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


# ============================================================
# Question 2: What percentage are international students?
# (to two decimal places)
# ============================================================
def query_2_international_percentage():
    """
    Calculates percentage of international students.
    
    Query: COUNT where us_or_international = 'International' / total COUNT
    
    Why: We need to count international entries and divide by total to get percentage.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM applicants")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM applicants WHERE us_or_international = 'International'")
    international = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM applicants WHERE us_or_international = 'American'")
    american = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM applicants WHERE us_or_international = 'Other'")
    other = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    percentage = round((international / total) * 100, 2) if total > 0 else 0
    
    return {
        'total': total,
        'international': international,
        'american': american,
        'other': other,
        'percentage': percentage
    }


# ============================================================
# Question 3: What is the average GPA, GRE, GRE V, GRE AW?
# ============================================================
def query_3_average_scores():
    """
    Calculates average scores for applicants who provided these metrics.
    
    Query: SELECT AVG(field) FROM applicants WHERE field IS NOT NULL
    
    Why: AVG function ignores NULL values, but we explicitly filter to be clear.
    Note: Many entries have NULL GRE scores (post-COVID, many programs made GRE optional).
    """
    conn = get_connection()
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
        'avg_gre_aw': avg_gre_aw
    }


# ============================================================
# Question 4: Average GPA of American students in Fall 2026?
# ============================================================
def query_4_american_fall_2026_gpa():
    """
    Returns average GPA for American students applying Fall 2026.
    
    Query: SELECT AVG(gpa) WHERE us_or_international = 'American' AND term = 'Fall 2026'
    
    Why: Filter by both nationality and term to get specific subset.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT AVG(gpa) FROM applicants 
        WHERE us_or_international = 'American' 
        AND term = 'Fall 2026'
        AND gpa IS NOT NULL
    """)
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


# ============================================================
# Question 5: What percent of Fall 2025 entries are Acceptances?
# (to two decimal places)
# ============================================================
def query_5_fall_2025_acceptance_rate():
    """
    Calculates acceptance rate for Fall 2025 applicants.
    
    Query: COUNT accepted / COUNT total WHERE term = 'Fall 2025'
    
    Why: Using ILIKE '%Accept%' to catch variations like "Accepted", "Acceptance via Email".
    """
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2025'")
    total = cur.fetchone()[0]
    
    cur.execute("""
        SELECT COUNT(*) FROM applicants 
        WHERE term = 'Fall 2025' 
        AND status ILIKE '%Accept%'
    """)
    accepted = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    percentage = round((accepted / total) * 100, 2) if total > 0 else 0
    
    return {
        'total': total,
        'accepted': accepted,
        'percentage': percentage
    }


# ============================================================
# Question 6: Average GPA of Fall 2026 acceptances?
# ============================================================
def query_6_fall_2026_acceptance_gpa():
    """
    Returns average GPA for accepted Fall 2026 applicants.
    
    Query: SELECT AVG(gpa) WHERE term = 'Fall 2026' AND status ILIKE '%Accept%'
    
    Why: Filter for both term and acceptance status.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT AVG(gpa) FROM applicants 
        WHERE term = 'Fall 2026'
        AND status ILIKE '%Accept%'
        AND gpa IS NOT NULL
    """)
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


# ============================================================
# Question 7: JHU Masters CS count?
# ============================================================
def query_7_jhu_masters_cs():
    """
    Counts applicants to JHU for Masters in Computer Science.
    
    Query: SELECT COUNT(*) WHERE program contains 'johns hopkins' or 'jhu' 
           AND 'computer science' AND degree contains 'master'
    
    Why: Search for both "Johns Hopkins" and "JHU" since users write either.
         The program field contains both program name and university combined.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM applicants 
        WHERE (program ILIKE '%johns hopkins%' OR program ILIKE '%jhu%')
        AND program ILIKE '%computer science%'
        AND degree ILIKE '%master%'
    """)
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


# ============================================================
# Question 8: 2026 PhD CS acceptances at top schools?
# ============================================================
def query_8_top_schools_phd_cs():
    """
    Counts 2026 PhD CS acceptances at Georgetown, MIT, Stanford, CMU.
    
    Query: SELECT COUNT(*) WHERE term contains '2026' AND status contains 'Accept'
           AND degree contains 'PhD' AND program contains 'computer science'
           AND program contains one of the university names
    
    Why: Using the raw 'program' field which contains both program and university.
         Multiple variations searched (mit, massachusetts institute, cmu, carnegie mellon).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM applicants 
        WHERE term ILIKE '%2026%'
        AND status ILIKE '%Accept%'
        AND degree ILIKE '%PhD%'
        AND program ILIKE '%computer science%'
        AND (
            program ILIKE '%georgetown%'
            OR program ILIKE '%mit%'
            OR program ILIKE '%massachusetts institute%'
            OR program ILIKE '%stanford%'
            OR program ILIKE '%carnegie mellon%'
            OR program ILIKE '%cmu%'
        )
    """)
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


# ============================================================
# Question 9: Same as Q8 but using LLM-generated fields?
# ============================================================
def query_9_top_schools_phd_cs_llm():
    """
    Same query as Q8, but uses LLM-generated university and program fields.
    
    Query: Uses llm_generated_program and llm_generated_university instead
    
    Why: The LLM separated university from program into distinct fields.
         This may give different results because LLM made classification decisions
         (e.g., MIT's "EECS" was classified as "Electrical Engineering" not "CS").
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) FROM applicants 
        WHERE term ILIKE '%2026%'
        AND status ILIKE '%Accept%'
        AND degree ILIKE '%PhD%'
        AND llm_generated_program ILIKE '%computer science%'
        AND (
            llm_generated_university ILIKE '%georgetown%'
            OR llm_generated_university ILIKE '%massachusetts institute%'
            OR llm_generated_university ILIKE '%mit%'
            OR llm_generated_university ILIKE '%stanford%'
            OR llm_generated_university ILIKE '%carnegie mellon%'
        )
    """)
    result = cur.fetchone()[0]
    cur.close()
    conn.close()
    return result


# ============================================================
# Custom Question 1: Top 10 most popular programs?
# ============================================================
def query_custom_1_top_programs():
    """
    What are the top 10 most popular programs by application count?
    
    Query: SELECT program, COUNT(*) GROUP BY program ORDER BY count DESC LIMIT 10
    
    Why: Using LLM-generated program names for cleaner grouping (avoids duplicates
         like "CS" vs "Computer Science" vs "Comp Sci").
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT llm_generated_program, COUNT(*) as count
        FROM applicants 
        WHERE llm_generated_program IS NOT NULL
        GROUP BY llm_generated_program
        ORDER BY count DESC
        LIMIT 10
    """)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


# ============================================================
# Custom Question 2: Acceptance rate by degree type?
# ============================================================
def query_custom_2_acceptance_by_degree():
    """
    What is the acceptance rate by degree type (PhD vs Masters vs others)?
    
    Query: SELECT degree, COUNT(*), SUM(accepted), rate GROUP BY degree
    
    Why: Compare competitiveness across degree types. PhD programs are typically
         more selective than Masters programs.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            degree,
            COUNT(*) as total,
            SUM(CASE WHEN status ILIKE '%Accept%' THEN 1 ELSE 0 END) as accepted,
            ROUND(100.0 * SUM(CASE WHEN status ILIKE '%Accept%' THEN 1 ELSE 0 END) / COUNT(*), 2) as rate
        FROM applicants
        WHERE degree IS NOT NULL
        GROUP BY degree
        ORDER BY total DESC
    """)
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results


# ============================================================
# Main function - runs all queries and prints results
# ============================================================
def run_all_queries():
    """Runs all queries and prints formatted results."""
    
    print("=" * 60)
    print("GRAD CAFE DATA ANALYSIS")
    print("Module 3 - Database Queries Assignment")
    print("=" * 60)
    
    # Q1
    q1 = query_1_fall_2026_count()
    print(f"\nQ1: Fall 2026 applicant count: {q1}")
    
    # Q2
    q2 = query_2_international_percentage()
    print(f"\nQ2: International percentage")
    print(f"    Total count: {q2['total']}")
    print(f"    International count: {q2['international']}")
    print(f"    American count: {q2['american']}")
    print(f"    Other count: {q2['other']}")
    print(f"    Percent International: {q2['percentage']}%")
    
    # Q3
    q3 = query_3_average_scores()
    print(f"\nQ3: Average scores")
    print(f"    Average GPA: {q3['avg_gpa']}")
    print(f"    Average GRE (Quant): {q3['avg_gre']}")
    print(f"    Average GRE V: {q3['avg_gre_v']}")
    print(f"    Average GRE AW: {q3['avg_gre_aw']}")
    
    # Q4
    q4 = query_4_american_fall_2026_gpa()
    print(f"\nQ4: Average GPA of American students in Fall 2026: {q4}")
    
    # Q5
    q5 = query_5_fall_2025_acceptance_rate()
    print(f"\nQ5: Fall 2025 acceptance rate")
    print(f"    Total Fall 2025 entries: {q5['total']}")
    print(f"    Accepted: {q5['accepted']}")
    print(f"    Acceptance percent: {q5['percentage']}%")
    
    # Q6
    q6 = query_6_fall_2026_acceptance_gpa()
    print(f"\nQ6: Average GPA of Fall 2026 Acceptances: {q6}")
    
    # Q7
    q7 = query_7_jhu_masters_cs()
    print(f"\nQ7: JHU Masters Computer Science count: {q7}")
    
    # Q8
    q8 = query_8_top_schools_phd_cs()
    print(f"\nQ8: 2026 PhD CS Acceptances (Georgetown/MIT/Stanford/CMU): {q8}")
    
    # Q9
    q9 = query_9_top_schools_phd_cs_llm()
    print(f"\nQ9: Same as Q8 using LLM fields: {q9}")
    if q9 != q8:
        print(f"    YES, the numbers changed! Difference: {q9 - q8}")
        print(f"    (LLM classified some EECS programs as 'Electrical Engineering')")
    else:
        print(f"    No change from Q8")
    
    # Custom Q1
    print(f"\nCustom Q1: Top 10 most popular programs")
    q10 = query_custom_1_top_programs()
    for i, (program, count) in enumerate(q10, 1):
        print(f"    {i}. {program}: {count}")
    
    # Custom Q2
    print(f"\nCustom Q2: Acceptance rate by degree type")
    q11 = query_custom_2_acceptance_by_degree()
    for degree, total, accepted, rate in q11:
        print(f"    {degree}: {rate}% ({accepted}/{total})")
    
    print("\n" + "=" * 60)
    
    return {
        'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4, 'q5': q5,
        'q6': q6, 'q7': q7, 'q8': q8, 'q9': q9,
        'q10': q10, 'q11': q11
    }


if __name__ == "__main__":
    run_all_queries()
