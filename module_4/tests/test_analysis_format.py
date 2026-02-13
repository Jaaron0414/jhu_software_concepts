"""
test_analysis_format.py - Analysis Formatting Tests

Verifies:
  - Every answer on the page is labeled with 'Answer:'
  - Percentages are displayed with exactly two decimal places
"""

import re
import pytest
from bs4 import BeautifulSoup


@pytest.mark.analysis
def test_all_answers_have_label(seeded_client):
    """Every .answer div starts with 'Answer:'."""
    soup = BeautifulSoup(
        seeded_client.get('/').data, 'html.parser'
    )
    answers = soup.find_all('div', class_='answer')
    assert len(answers) >= 1
    for div in answers:
        assert 'Answer:' in div.get_text(), (
            f"Missing 'Answer:' in: {div.get_text()[:80]}"
        )


@pytest.mark.analysis
def test_percentages_have_two_decimals(seeded_client):
    """Any percentage on the page uses exactly two decimal places."""
    html = seeded_client.get('/').data.decode()
    # Match patterns like "40.00%", "3.95%" — digits.digits%
    percentages = re.findall(r'(\d+\.\d+)%', html)
    assert len(percentages) >= 1, "No percentages found on the page"
    for pct in percentages:
        decimals = pct.split('.')[1]
        assert len(decimals) == 2, (
            f"Percentage '{pct}%' does not have two decimal places"
        )


@pytest.mark.analysis
def test_page_shows_at_least_one_numeric_answer(seeded_client):
    """The page contains at least one numeric answer value."""
    html = seeded_client.get('/').data.decode()
    # Look for digits that follow "Answer:"
    assert re.search(r'Answer:\s*\d', html), (
        "No numeric answer found after 'Answer:'"
    )


@pytest.mark.analysis
def test_answer_count_matches_questions(seeded_client):
    """There should be at least 11 Answer: labels (Q1-Q9 + 2 custom)."""
    html = seeded_client.get('/').data.decode()
    count = html.count('Answer:')
    assert count >= 11, f"Expected >=11 Answer: labels, found {count}"
