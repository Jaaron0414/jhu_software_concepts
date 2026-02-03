"""
Data Cleaning Module
Cleans and standardizes Grad Cafe applicant data.
- Formats GPA, GRE scores, dates
- Separates program and university names
- Removes HTML and standardizes missing data
- Can optionally use LLM for name standardization

Main functions:
- clean_data(): main cleaner
- save_cleaned_data() / load_cleaned_data(): JSON I/O
"""

import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


def clean_data(raw_data: List[Dict[str, Any]], 
               use_llm: bool = False,
               llm_config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Clean raw Grad Cafe data.
    Standardizes formats, removes HTML, separates program/university.
    
    Args:
        raw_data: Raw applicant data from scraper
        use_llm: Whether to use LLM for name standardization
        llm_config: Config for LLM (if used)
        
    Returns:
        List of cleaned applicant dicts
    """
    print(f"Cleaning {len(raw_data)} entries...")
    
    cleaned_data = []
    
    for i, entry in enumerate(raw_data):
        try:
            # Create cleaned version, preserve original for traceability
            cleaned_entry = {
                # Keep originals
                'original_program': entry.get('program'),
                'original_status': entry.get('status'),
                
                # Cleaned versions
                'program': entry.get('program'),
                'university': None,
                'cleaned_program': None,
                'cleaned_university': None,
                'degree': _extract_degree_info(entry.get('degree')),
                'status': _clean_status(entry.get('status')),
                'date_added': _parse_date(entry.get('date')),
                'gpa': _standardize_gpa(entry.get('gpa')),
                'gre_verbal': _standardize_gre_score(entry.get('gre_verbal')),
                'gre_quantitative': _standardize_gre_score(entry.get('gre_quantitative')),
                'gre_aw': _standardize_gre_score(entry.get('gre_aw')),
                'gre_subject': _standardize_gre_score(entry.get('gre_subject')),
                'comments': _remove_html_tags(entry.get('comments')),
                'url': entry.get('url'),
                'entry_link': entry.get('entry_link'),
                'international': entry.get('international'),
                'semester_year': entry.get('semester_year'),
                'acceptance_date': entry.get('acceptance_date'),
                'rejection_date': entry.get('rejection_date'),
            }
            
            # Try to split program and university
            program, university = _parse_program_university(entry.get('program', ''))
            cleaned_entry['program'] = program
            cleaned_entry['university'] = university
            
            cleaned_data.append(cleaned_entry)
            
            if (i + 1) % 1000 == 0:
                print(f"  Processed {i + 1} entries...")
        
        except Exception as e:
            print(f"  Warning: Error on entry {i}: {e}")
            continue
    
    print(f"Cleaned {len(cleaned_data)} entries successfully")
    
    # Use LLM if requested
    if use_llm and llm_config:
        cleaned_data = _apply_llm_standardization(cleaned_data, llm_config)
    
    return cleaned_data


def _parse_program_university(program_field: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Try to split program and university from mixed field.
    Grad Cafe puts them together so we need to parse them out.
    """
    if not program_field:
        return None, None
    
    program_field = program_field.strip()
    
    # Try "Program at University" format
    at_pattern = r'(.+?)\s+at\s+(.+)'
    at_match = re.search(at_pattern, program_field, re.IGNORECASE)
    if at_match:
        return at_match.group(1).strip(), at_match.group(2).strip()
    
    # Try "Program (University)" format
    paren_pattern = r'(.+?)\s*\((.+?)\)'
    paren_match = re.search(paren_pattern, program_field)
    if paren_match:
        return paren_match.group(1).strip(), paren_match.group(2).strip()
    
    # Try comma separation
    if ',' in program_field:
        parts = program_field.split(',', 1)
        return parts[0].strip(), parts[1].strip()
    
    # If nothing matches, just return it as program
    return program_field, None


def _standardize_gre_score(score: Optional[str]) -> Optional[str]:
    """
    Clean up GRE scores.
    Extract digits and validate they're in reasonable range.
    """
    if not score or not isinstance(score, str):
        return None
    
    # Get just the digits
    score_clean = re.sub(r'[^\d]', '', score.strip())
    
    if not score_clean:
        return None
    
    try:
        score_int = int(score_clean)
        # Check if it's in valid range (0-170 for Q/V, 0-6 for AW, 0-800 for old format)
        if 0 <= score_int <= 800:
            return str(score_int)
    except ValueError:
        pass
    
    return None


def _standardize_gpa(gpa: Optional[str]) -> Optional[str]:
    """
    Clean up GPA values.
    Extract the number and validate it's between 0-4.0
    """
    if not gpa or not isinstance(gpa, str):
        return None
    
    gpa_clean = gpa.strip()
    
    # Extract numeric value (handles "3.95" or "3.95/4.0" formats)
    match = re.search(r'(\d+\.?\d*)', gpa_clean)
    
    if match:
        try:
            gpa_float = float(match.group(1))
            # Check valid range
            if 0 <= gpa_float <= 4.0:
                return f"{gpa_float:.2f}"
        except ValueError:
            pass
    
    return None


def _extract_degree_info(degree_field: Optional[str]) -> Optional[str]:
    """Standardize degree types (MS, PhD, etc)."""
    if not degree_field:
        return None
    
    degree_upper = degree_field.upper().strip()
    
    if 'PhD' in degree_upper or 'PHARM' in degree_upper or 'DDS' in degree_upper:
        return 'PhD'
    elif 'MS' in degree_upper or 'M.S' in degree_upper or 'MASTER' in degree_upper:
        return 'MS'
    elif 'MBA' in degree_upper:
        return 'MBA'
    elif 'MD' in degree_upper:
        return 'MD'
    else:
        return 'Other'


def _clean_status(status: Optional[str]) -> Optional[str]:
    """Standardize admission status."""
    if not status:
        return None
    
    status_upper = status.upper().strip()
    
    if 'ACCEPT' in status_upper:
        return 'Accepted'
    elif 'REJECT' in status_upper:
        return 'Rejected'
    elif 'WAITLIST' in status_upper:
        return 'Waitlisted'
    else:
        return status.strip()


def _parse_date(date_str: Optional[str]) -> Optional[str]:
    """
    Convert date strings to ISO format (YYYY-MM-DD).
    Handles various formats (MM/DD/YYYY, YYYY-MM-DD, etc).
    """
    if not date_str or not isinstance(date_str, str):
        return None
    
    date_str = date_str.strip()
    
    # Common date formats from Grad Cafe
    date_patterns = [
        r'(\d{1,2})/(\d{1,2})/(\d{4})',      # MM/DD/YYYY
        r'(\d{4})-(\d{1,2})-(\d{1,2})',      # YYYY-MM-DD
        r'(\d{1,2})-(\d{1,2})-(\d{2,4})',    # DD-MM-YY(YY)
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                groups = match.groups()
                # Handle different formats
                if len(groups[2]) == 4:  # MM/DD/YYYY format
                    month, day, year = groups
                elif len(groups[0]) == 4:  # YYYY-MM-DD format
                    year, month, day = groups
                else:
                    continue
                
                year = int(year)
                month = int(month)
                day = int(day)
                
                # Fix 2-digit years
                if year < 100:
                    year = 2000 + year if year < 50 else 1900 + year
                
                # Check valid date
                date_obj = datetime(year, month, day)
                return date_obj.strftime('%Y-%m-%d')
            except (ValueError, IndexError):
                continue
    
    return None


def _remove_html_tags(text: Optional[str]) -> Optional[str]:
    """Remove HTML tags and entities from text."""
    if not text:
        return None
    
    # Remove tags
    text_clean = re.sub(r'<[^>]+>', '', text)
    
    # Remove entities
    text_clean = text_clean.replace('&lt;', '<')
    text_clean = text_clean.replace('&gt;', '>')
    text_clean = text_clean.replace('&amp;', '&')
    text_clean = text_clean.replace('&quot;', '"')
    text_clean = text_clean.replace('&#39;', "'")
    
    # Clean whitespace
    text_clean = ' '.join(text_clean.split())
    
    return text_clean.strip() if text_clean.strip() else None


def _apply_llm_standardization(cleaned_data: List[Dict[str, Any]], 
                               llm_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Placeholder for LLM-based name standardization.
    The actual work happens via the llm_hosting module separately.
    """
    print("\nNote: Run LLM standardization separately using:")
    print("  cd llm_hosting")
    print("  python app.py --file \"applicant_data.json\" > output.json")
    print("\nThen merge results into your dataset.")
    
    return cleaned_data


def save_cleaned_data(data: List[Dict[str, Any]], 
                      filename: str = 'applicant_data_cleaned.json') -> str:
    """Save cleaned data to JSON."""
    output_dir = os.path.dirname(filename)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(data)} cleaned entries to {filename}")
    return filename


def load_cleaned_data(filename: str = 'applicant_data_cleaned.json') -> List[Dict[str, Any]]:
    """Load cleaned data from JSON."""
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return []
    
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} cleaned entries from {filename}")
    return data


def main():
    """Main function - run data cleaning."""
    # Load raw data
    raw_data = json.load(open('applicant_data.json', 'r'))
    
    # Clean it
    cleaned = clean_data(raw_data, use_llm=False)
    
    # Save cleaned data
    save_cleaned_data(cleaned, 'applicant_data_cleaned.json')
    
    print("\nDone cleaning!")
    print("Next: Use LLM service to standardize program and university names")
    print("See llm_hosting/ folder for instructions")


if __name__ == "__main__":
    main()
