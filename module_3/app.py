"""
app.py - Module 3 Assignment
JHU Modern Software Concepts

Flask web application that displays Grad Cafe data analysis results.
Includes buttons to pull new data and refresh analysis.

Author: Student
Date: February 2026

To run: python app.py
Then open http://localhost:5000 in your browser
"""

from flask import Flask, render_template, jsonify
import psycopg2
import subprocess
import threading
import os
import sys

# Create Flask app
app = Flask(__name__)

# Database connection settings
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'gradcafe'
DB_USER = 'postgres'
DB_PASSWORD = '196301'

# Track if scraping is running (for the Pull Data button)
scraping_status = {
    'is_running': False,
    'message': ''
}


def get_db_connection():
    """Creates and returns a database connection."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def get_analysis_results():
    """
    Runs all the analysis queries and returns results as a dictionary.
    This function is called when the page loads or is refreshed.
    """
    results = {}
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Q1: Fall 2026 count
    cur.execute("SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2026'")
    results['q1_fall_2026_count'] = cur.fetchone()[0]
    
    # Q2: International percentage
    cur.execute("SELECT COUNT(*) FROM applicants")
    total = cur.fetchone()[0]
    results['total_count'] = total
    
    cur.execute("SELECT COUNT(*) FROM applicants WHERE us_or_international = 'International'")
    results['international_count'] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM applicants WHERE us_or_international = 'American'")
    results['american_count'] = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM applicants WHERE us_or_international = 'Other'")
    results['other_count'] = cur.fetchone()[0]
    
    results['international_percentage'] = round(
        (results['international_count'] / total) * 100, 2
    ) if total > 0 else 0
    
    # Q3: Average scores
    cur.execute("SELECT AVG(gpa) FROM applicants WHERE gpa IS NOT NULL")
    results['avg_gpa'] = cur.fetchone()[0]
    
    cur.execute("SELECT AVG(gre) FROM applicants WHERE gre IS NOT NULL")
    results['avg_gre'] = cur.fetchone()[0]
    
    cur.execute("SELECT AVG(gre_v) FROM applicants WHERE gre_v IS NOT NULL")
    results['avg_gre_v'] = cur.fetchone()[0]
    
    cur.execute("SELECT AVG(gre_aw) FROM applicants WHERE gre_aw IS NOT NULL")
    results['avg_gre_aw'] = cur.fetchone()[0]
    
    # Q4: American Fall 2026 GPA
    cur.execute("""
        SELECT AVG(gpa) FROM applicants 
        WHERE us_or_international = 'American' 
        AND term = 'Fall 2026'
        AND gpa IS NOT NULL
    """)
    results['american_fall_2026_gpa'] = cur.fetchone()[0]
    
    # Q5: Fall 2025 acceptance rate
    cur.execute("SELECT COUNT(*) FROM applicants WHERE term = 'Fall 2025'")
    fall_2025_total = cur.fetchone()[0]
    results['fall_2025_total'] = fall_2025_total
    
    cur.execute("""
        SELECT COUNT(*) FROM applicants 
        WHERE term = 'Fall 2025' AND status ILIKE '%Accept%'
    """)
    results['fall_2025_accepted'] = cur.fetchone()[0]
    results['fall_2025_acceptance_rate'] = round(
        (results['fall_2025_accepted'] / fall_2025_total) * 100, 2
    ) if fall_2025_total > 0 else 0
    
    # Q6: Fall 2026 acceptance GPA
    cur.execute("""
        SELECT AVG(gpa) FROM applicants 
        WHERE term = 'Fall 2026'
        AND status ILIKE '%Accept%'
        AND gpa IS NOT NULL
    """)
    results['fall_2026_acceptance_gpa'] = cur.fetchone()[0]
    
    # Q7: JHU Masters CS
    cur.execute("""
        SELECT COUNT(*) FROM applicants 
        WHERE (program ILIKE '%johns hopkins%' OR program ILIKE '%jhu%')
        AND program ILIKE '%computer science%'
        AND degree ILIKE '%master%'
    """)
    results['jhu_masters_cs'] = cur.fetchone()[0]
    
    # Q8: Top schools PhD CS
    cur.execute("""
        SELECT COUNT(*) FROM applicants 
        WHERE term ILIKE '%2026%'
        AND status ILIKE '%Accept%'
        AND degree ILIKE '%PhD%'
        AND program ILIKE '%computer science%'
        AND (
            program ILIKE '%georgetown%' OR program ILIKE '%mit%'
            OR program ILIKE '%massachusetts institute%'
            OR program ILIKE '%stanford%'
            OR program ILIKE '%carnegie mellon%' OR program ILIKE '%cmu%'
        )
    """)
    results['phd_cs_top_schools'] = cur.fetchone()[0]
    
    # Q9: Using LLM fields (cleaner but may classify programs differently)
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
    results['phd_cs_top_schools_llm'] = cur.fetchone()[0]
    
    # Custom Q1: Top programs
    cur.execute("""
        SELECT llm_generated_program, COUNT(*) as count
        FROM applicants WHERE llm_generated_program IS NOT NULL
        GROUP BY llm_generated_program
        ORDER BY count DESC LIMIT 10
    """)
    results['top_programs'] = cur.fetchall()
    
    # Custom Q2: Acceptance by degree
    cur.execute("""
        SELECT degree, COUNT(*) as total,
            SUM(CASE WHEN status ILIKE '%Accept%' THEN 1 ELSE 0 END) as accepted,
            ROUND(100.0 * SUM(CASE WHEN status ILIKE '%Accept%' THEN 1 ELSE 0 END) / COUNT(*), 2) as rate
        FROM applicants WHERE degree IS NOT NULL
        GROUP BY degree ORDER BY total DESC
    """)
    results['acceptance_by_degree'] = cur.fetchall()
    
    cur.close()
    conn.close()
    return results


def run_scraper_background():
    """
    Runs the web scraper in a background thread.
    This is called when user clicks 'Pull Data' button.
    """
    global scraping_status
    scraping_status['is_running'] = True
    scraping_status['message'] = 'Scraping new data from Grad Cafe...'
    
    try:
        # Run the scraper script
        script_dir = os.path.dirname(__file__)
        result = subprocess.run(
            [sys.executable, '-c', f'''
import sys
sys.path.insert(0, r"{script_dir}")
from scrape import scrape_data, save_data
data = scrape_data(result_type='all', num_pages=10, delay=0.5)
if data:
    save_data(data, r"{script_dir}/scraped_data.json")
    print(f"Scraped {{len(data)}} entries")
'''],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            scraping_status['message'] = 'Scraping completed! Click Update Analysis.'
        else:
            scraping_status['message'] = f'Scraping failed: {result.stderr}'
            
    except subprocess.TimeoutExpired:
        scraping_status['message'] = 'Scraping timed out (5 min limit)'
    except Exception as e:
        scraping_status['message'] = f'Error: {str(e)}'
    finally:
        scraping_status['is_running'] = False


# ============================================================
# Flask Routes
# ============================================================

@app.route('/')
def index():
    """Main page - shows analysis results."""
    results = get_analysis_results()
    return render_template('index.html', results=results, scraping_status=scraping_status)


@app.route('/pull_data', methods=['POST'])
def pull_data():
    """
    API endpoint for Pull Data button.
    Starts scraping in background thread.
    """
    global scraping_status
    
    if scraping_status['is_running']:
        return jsonify({
            'success': False,
            'message': 'Scraping is already running. Please wait.'
        })
    
    # Start scraper in background
    thread = threading.Thread(target=run_scraper_background)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Started scraping. This may take a few minutes.'
    })


@app.route('/update_analysis', methods=['POST'])
def update_analysis():
    """
    API endpoint for Update Analysis button.
    Reloads data if not currently scraping.
    """
    global scraping_status
    
    if scraping_status['is_running']:
        return jsonify({
            'success': False,
            'message': 'Cannot update while scraping is running.'
        })
    
    return jsonify({
        'success': True,
        'message': 'Analysis updated!'
    })


@app.route('/status')
def status():
    """Returns current scraping status (for AJAX polling)."""
    return jsonify(scraping_status)


# ============================================================
# Run the app
# ============================================================
if __name__ == '__main__':
    print("Starting Flask server...")
    print("Open http://localhost:5000 in your browser")
    print("Press Ctrl+C to stop")
    app.run(debug=True, port=5000)
