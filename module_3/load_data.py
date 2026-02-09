"""
load_data.py - Module 3 Assignment
JHU Modern Software Concepts

This script loads the cleaned Grad Cafe applicant data from Module 2
into a PostgreSQL database for analysis.

Author: Student
Date: February 2026
"""

import json
import psycopg2
from psycopg2.extras import execute_values
import os

# Database connection configuration
# Note: In production, these should be environment variables
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'gradcafe'
DB_USER = 'postgres'
DB_PASSWORD = '196301'


def connect_to_database():
    """
    Establishes connection to PostgreSQL database.
    Returns the connection object.
    """
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        print(f"Connected to database: {DB_NAME}")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


def create_table(cursor):
    """
    Creates the applicants table with the required schema.
    Drops existing table if it exists to start fresh.
    """
    # SQL statement to create the table
    # Following the schema from the assignment requirements
    create_sql = """
    DROP TABLE IF EXISTS applicants;
    
    CREATE TABLE applicants (
        p_id SERIAL PRIMARY KEY,
        program TEXT,
        comments TEXT,
        date_added DATE,
        url TEXT,
        status TEXT,
        term TEXT,
        us_or_international TEXT,
        gpa FLOAT,
        gre FLOAT,
        gre_v FLOAT,
        gre_aw FLOAT,
        degree TEXT,
        llm_generated_program TEXT,
        llm_generated_university TEXT
    );
    
    -- Create indexes to speed up queries
    CREATE INDEX idx_term ON applicants(term);
    CREATE INDEX idx_status ON applicants(status);
    CREATE INDEX idx_us_or_international ON applicants(us_or_international);
    """
    
    cursor.execute(create_sql)
    print("Created applicants table")


def convert_international_status(is_international):
    """
    Converts boolean international flag to text format.
    Returns 'International', 'American', or 'Other'.
    """
    if is_international is None:
        return 'Other'
    elif is_international == True:
        return 'International'
    else:
        return 'American'


def safe_float(value):
    """
    Safely converts a value to float.
    Returns None if conversion fails.
    """
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def load_json_data(filepath):
    """
    Loads JSON data from file.
    Returns list of entries or empty list if file not found.
    """
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} entries from {filepath}")
    return data


def prepare_row(entry):
    """
    Prepares a single entry for database insertion.
    Combines program and university fields as required.
    """
    # Combine program and university into single field
    university = entry.get('university', '') or ''
    program = entry.get('program', '') or ''
    combined = f"{program}, {university}".strip(', ').lower()
    
    # Build the row tuple
    row = (
        combined if combined else None,                      # program
        entry.get('comments'),                               # comments
        None,                                                # date_added
        entry.get('url') or entry.get('entry_link'),        # url
        entry.get('status'),                                 # status
        entry.get('semester_year'),                          # term
        convert_international_status(entry.get('international')),
        safe_float(entry.get('gpa')),                        # gpa
        safe_float(entry.get('gre_quantitative')),           # gre
        safe_float(entry.get('gre_verbal')),                 # gre_v
        safe_float(entry.get('gre_aw')),                     # gre_aw
        entry.get('degree'),                                 # degree
        entry.get('llm_generated_program'),
        entry.get('llm_generated_university'),
    )
    return row


def insert_data(cursor, data):
    """
    Inserts all data into the database using bulk insert.
    This is much faster than inserting one row at a time.
    """
    # Prepare all rows
    rows = [prepare_row(entry) for entry in data]
    
    # SQL for bulk insert
    insert_sql = """
        INSERT INTO applicants (
            program, comments, date_added, url, status, term,
            us_or_international, gpa, gre, gre_v, gre_aw, degree,
            llm_generated_program, llm_generated_university
        ) VALUES %s
    """
    
    # Use execute_values for efficient bulk insert
    execute_values(cursor, insert_sql, rows, page_size=1000)
    print(f"Inserted {len(rows)} rows")


def print_statistics(cursor):
    """
    Prints some basic statistics about the loaded data.
    Useful for verifying the data was loaded correctly.
    """
    print("\n--- Data Statistics ---")
    
    cursor.execute("SELECT COUNT(*) FROM applicants")
    total = cursor.fetchone()[0]
    print(f"Total entries: {total}")
    
    cursor.execute("SELECT COUNT(*) FROM applicants WHERE gpa IS NOT NULL")
    gpa_count = cursor.fetchone()[0]
    print(f"Entries with GPA: {gpa_count}")
    
    cursor.execute("SELECT COUNT(*) FROM applicants WHERE gre IS NOT NULL")
    gre_count = cursor.fetchone()[0]
    print(f"Entries with GRE: {gre_count}")
    
    cursor.execute("SELECT COUNT(*) FROM applicants WHERE comments IS NOT NULL")
    comments_count = cursor.fetchone()[0]
    print(f"Entries with comments: {comments_count}")


def main():
    """
    Main function - orchestrates the data loading process.
    """
    print("=" * 50)
    print("Loading Grad Cafe Data into PostgreSQL")
    print("=" * 50)
    
    # Find the JSON file from module_2
    json_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 'module_2', 
        'llm_extend_applicant_data.json'
    )
    
    # Load the data
    data = load_json_data(json_path)
    if not data:
        print("No data to load. Exiting.")
        return
    
    # Connect to database
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        # Create table and insert data
        create_table(cursor)
        insert_data(cursor, data)
        
        # Commit changes
        conn.commit()
        
        # Show statistics
        print_statistics(cursor)
        
        print("\nData loaded successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()
        print("Database connection closed.")


if __name__ == "__main__":
    main()
