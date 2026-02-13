"""
test_clean.py - Data Cleaning Module Tests

Achieves coverage for src/clean.py.
"""

import json
import pytest

from src.clean import (
    clean_data,
    parse_program_university,
    standardize_gre,
    standardize_gpa,
    clean_status,
    parse_date,
    remove_html,
    save_cleaned_data,
    load_cleaned_data,
)


# ---------------------------------------------------------------------------
# clean_data
# ---------------------------------------------------------------------------

@pytest.mark.web
def test_clean_data_basic():
    """clean_data processes a list of raw entries."""
    raw = [
        {
            'program': 'CS',
            'university': 'MIT',
            'degree': 'PhD',
            'status': 'Accepted',
            'date': '01/15/2026',
            'gpa': '3.95',
            'gre_verbal': '165',
            'gre_quantitative': '170',
            'gre_aw': '5.0',
            'comments': '<b>Great</b>',
            'url': 'http://x',
            'entry_link': 'http://x',
            'international': True,
            'semester_year': 'Fall 2026',
        }
    ]
    result = clean_data(raw)
    assert len(result) == 1
    assert result[0]['status'] == 'Accepted'
    assert result[0]['gpa'] == '3.95'
    assert result[0]['comments'] == 'Great'


@pytest.mark.web
def test_clean_data_skips_bad_entry():
    """clean_data skips entries that raise exceptions."""
    raw = [
        None,    # will cause AttributeError on .get()
        {'program': 'P', 'status': 'Rejected', 'gpa': None,
         'gre_verbal': None, 'gre_quantitative': None,
         'gre_aw': None, 'comments': None, 'url': None,
         'entry_link': None, 'international': None,
         'semester_year': None, 'university': None,
         'degree': None, 'date': None},
    ]
    result = clean_data(raw)
    assert len(result) == 1


@pytest.mark.web
def test_clean_data_llm_flag(capsys):
    """clean_data prints LLM reminder when use_llm=True."""
    clean_data([], use_llm=True)
    out = capsys.readouterr().out
    assert 'LLM' in out


# ---------------------------------------------------------------------------
# parse_program_university
# ---------------------------------------------------------------------------

@pytest.mark.web
def test_parse_at_format():
    """'CS at MIT' => ('CS', 'MIT')."""
    assert parse_program_university('CS at MIT') == ('CS', 'MIT')


@pytest.mark.web
def test_parse_paren_format():
    """'CS (MIT)' => ('CS', 'MIT')."""
    assert parse_program_university('CS (MIT)') == ('CS', 'MIT')


@pytest.mark.web
def test_parse_comma_format():
    """'CS, MIT' => ('CS', 'MIT')."""
    assert parse_program_university('CS, MIT') == ('CS', 'MIT')


@pytest.mark.web
def test_parse_single_value():
    """'CS' => ('CS', None)."""
    assert parse_program_university('CS') == ('CS', None)


@pytest.mark.web
def test_parse_none():
    """None => (None, None)."""
    assert parse_program_university(None) == (None, None)


# ---------------------------------------------------------------------------
# standardize_gre
# ---------------------------------------------------------------------------

@pytest.mark.web
def test_standardize_gre_valid():
    assert standardize_gre('165') == '165'


@pytest.mark.web
def test_standardize_gre_invalid():
    assert standardize_gre(None) is None
    assert standardize_gre('') is None
    assert standardize_gre(123) is None     # not a string
    assert standardize_gre('abc') is None   # no digits at all


@pytest.mark.web
def test_standardize_gre_with_text():
    """GRE score embedded in text is extracted."""
    assert standardize_gre('170pts') == '170'


@pytest.mark.web
def test_standardize_gre_too_high():
    """Values > 800 are rejected."""
    assert standardize_gre('999') is None


@pytest.mark.web
def test_standardize_gre_zero():
    """Zero is a valid GRE score."""
    assert standardize_gre('0') == '0'


# ---------------------------------------------------------------------------
# standardize_gpa
# ---------------------------------------------------------------------------

@pytest.mark.web
def test_standardize_gpa_valid():
    assert standardize_gpa('3.95') == '3.95'
    assert standardize_gpa('4.0') == '4.00'


@pytest.mark.web
def test_standardize_gpa_out_of_range():
    assert standardize_gpa('5.5') is None


@pytest.mark.web
def test_standardize_gpa_none():
    assert standardize_gpa(None) is None
    assert standardize_gpa('') is None
    assert standardize_gpa(3.5) is None     # not a string


# ---------------------------------------------------------------------------
# clean_status
# ---------------------------------------------------------------------------

@pytest.mark.web
def test_clean_status_accepted():
    assert clean_status('Accepted via Email') == 'Accepted'


@pytest.mark.web
def test_clean_status_rejected():
    assert clean_status('Rejected') == 'Rejected'


@pytest.mark.web
def test_clean_status_waitlisted():
    assert clean_status('Waitlisted') == 'Waitlisted'


@pytest.mark.web
def test_clean_status_other():
    assert clean_status('Interview') == 'Interview'


@pytest.mark.web
def test_clean_status_none():
    assert clean_status(None) is None


# ---------------------------------------------------------------------------
# parse_date
# ---------------------------------------------------------------------------

@pytest.mark.web
def test_parse_date_us_format():
    assert parse_date('01/15/2026') == '2026-01-15'


@pytest.mark.web
def test_parse_date_iso_format():
    assert parse_date('2026-01-15') == '2026-01-15'


@pytest.mark.web
def test_parse_date_invalid():
    assert parse_date('not-a-date') is None
    assert parse_date(None) is None
    assert parse_date('') is None
    assert parse_date(42) is None


@pytest.mark.web
def test_parse_date_bad_values():
    """Invalid day/month still returns None."""
    assert parse_date('13/32/2026') is None


@pytest.mark.web
def test_parse_date_iso_bad_values():
    """Invalid ISO date returns None."""
    assert parse_date('2026-13-01') is None


# ---------------------------------------------------------------------------
# remove_html
# ---------------------------------------------------------------------------

@pytest.mark.web
def test_remove_html_tags():
    assert remove_html('<b>Hello</b>') == 'Hello'


@pytest.mark.web
def test_remove_html_entities():
    assert remove_html('a &amp; b') == 'a & b'
    assert remove_html('&lt;tag&gt;') == '<tag>'
    assert remove_html('&quot;hi&quot;') == '"hi"'
    assert remove_html("it&#39;s") == "it's"


@pytest.mark.web
def test_remove_html_none():
    assert remove_html(None) is None
    assert remove_html('') is None


# ---------------------------------------------------------------------------
# save / load
# ---------------------------------------------------------------------------

@pytest.mark.web
def test_save_and_load_cleaned(tmp_path):
    fp = str(tmp_path / 'cleaned.json')
    data = [{'a': 1}]
    save_cleaned_data(data, fp)
    assert load_cleaned_data(fp) == data


@pytest.mark.web
def test_load_cleaned_missing():
    assert load_cleaned_data('/no/such/file.json') == []


@pytest.mark.web
def test_save_creates_dirs(tmp_path):
    fp = str(tmp_path / 'sub' / 'data.json')
    save_cleaned_data([1], fp)
    assert load_cleaned_data(fp) == [1]
