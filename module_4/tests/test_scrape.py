"""
test_scrape.py - Tests for the web scraper.

All network calls are mocked (we never actually hit Grad Cafe).
Uses fake HTML that mirrors the real page structure.

Author: Aaron Xu
"""

import json
import os
import pytest
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError

from src.scrape import (
    scrape_data,
    extract_entries,
    parse_main_row,
    parse_additional_row,
    clean_text,
    save_data,
    load_data,
)


# --- Fake HTML that looks like a real Grad Cafe page ---

FAKE_HTML = """
<html><body>
<table><tbody>
<tr>
  <td><div class="tw-font-medium">MIT</div></td>
  <td><span>Computer Science</span><span class="tw-text-gray-500">PhD</span></td>
  <td>01/15/2026</td>
  <td><div class="tw-inline-flex">Accepted</div></td>
  <td><a href="/result/123">view</a></td>
</tr>
<tr class="tw-border-none">
  <td colspan="5">
    <div class="tw-inline-flex">Fall 2026</div>
    <div class="tw-inline-flex">GPA 3.95</div>
    <div class="tw-inline-flex">American</div>
    <div class="tw-inline-flex">GRE Q 170</div>
    <div class="tw-inline-flex">GRE V 165</div>
    <div class="tw-inline-flex">AW 5.0</div>
    <p class="tw-text-gray-500">Great school!</p>
  </td>
</tr>
</tbody></table>
</body></html>
"""

EMPTY_HTML = "<html><body><table><tbody></tbody></table></body></html>"
NO_TBODY_HTML = "<html><body></body></html>"


# --- Parsing tests ---

@pytest.mark.web
def test_extract_entries_basic():
    """Should pull out one entry from our fake HTML."""
    entries = extract_entries(FAKE_HTML)
    assert len(entries) == 1
    e = entries[0]
    assert e['university'] == 'MIT'
    assert e['program'] == 'Computer Science'
    assert e['degree'] == 'PhD'
    assert e['status'] == 'Accepted'
    assert e['semester_year'] == 'Fall 2026'
    assert e['gpa'] == '3.95'
    assert e['international'] is False
    assert e['gre_quantitative'] == '170'
    assert e['gre_verbal'] == '165'
    assert e['gre_aw'] == '5.0'
    assert e['comments'] == 'Great school!'
    assert '/result/123' in e['entry_link']


@pytest.mark.web
def test_extract_entries_empty():
    """extract_entries returns [] when tbody is empty."""
    assert extract_entries(EMPTY_HTML) == []


@pytest.mark.web
def test_extract_entries_no_tbody():
    """extract_entries returns [] when no tbody element."""
    assert extract_entries(NO_TBODY_HTML) == []


@pytest.mark.web
def test_extract_entries_few_tds():
    """Rows with fewer than 4 <td>s should be skipped."""
    html = """
    <html><body><table><tbody>
    <tr><td>Only one</td></tr>
    <tr><td>A</td><td>B</td></tr>
    </tbody></table></body></html>
    """
    assert extract_entries(html) == []


@pytest.mark.web
def test_parse_main_row_no_spans():
    """If there are no <span>s, program text comes from the whole <td>."""
    from bs4 import BeautifulSoup
    html = """
    <tr>
      <td>University</td>
      <td>Program Only</td>
      <td>2026-01-01</td>
      <td>Rejected</td>
    </tr>
    """
    soup = BeautifulSoup(html, 'html.parser')
    row = soup.find('tr')
    tds = row.find_all('td')
    entry = parse_main_row(row, tds)
    assert entry['university'] == 'University'
    assert entry['program'] == 'Program Only'
    assert entry['status'] == 'Rejected'
    assert entry['entry_link'] is None


@pytest.mark.web
def test_parse_main_row_absolute_link():
    """parse_main_row handles absolute href."""
    from bs4 import BeautifulSoup
    html = """
    <tr>
      <td>U</td><td><span>P</span></td><td>D</td><td>S</td>
      <td><a href="https://example.com/result/99">v</a></td>
    </tr>
    """
    soup = BeautifulSoup(html, 'html.parser')
    row = soup.find('tr')
    tds = row.find_all('td')
    entry = parse_main_row(row, tds)
    assert entry['entry_link'] == 'https://example.com/result/99'


@pytest.mark.web
def test_parse_additional_row_international():
    """parse_additional_row detects International status."""
    from bs4 import BeautifulSoup
    html = """
    <tr class="tw-border-none">
      <td><div class="tw-inline-flex">International</div></td>
    </tr>
    """
    soup = BeautifulSoup(html, 'html.parser')
    row = soup.find('tr')
    entry = {'international': None}
    parse_additional_row(row, entry)
    assert entry['international'] is True


@pytest.mark.web
def test_parse_additional_row_gre_out_of_range():
    """A GRE score of 50 is way out of range and should be ignored."""
    from bs4 import BeautifulSoup
    html = """
    <tr class="tw-border-none">
      <td><div class="tw-inline-flex">GRE Q 50</div></td>
    </tr>
    """
    soup = BeautifulSoup(html, 'html.parser')
    row = soup.find('tr')
    entry = {'gre_quantitative': None, 'gre_verbal': None}
    parse_additional_row(row, entry)
    assert entry['gre_quantitative'] is None


@pytest.mark.web
def test_parse_additional_row_empty_tag():
    """parse_additional_row ignores empty tag divs."""
    from bs4 import BeautifulSoup
    html = """
    <tr class="tw-border-none">
      <td><div class="tw-inline-flex">   </div></td>
    </tr>
    """
    soup = BeautifulSoup(html, 'html.parser')
    row = soup.find('tr')
    entry = {}
    parse_additional_row(row, entry)  # should not crash


@pytest.mark.web
def test_parse_additional_row_short_comment():
    """Comments with <=1 char are not stored."""
    from bs4 import BeautifulSoup
    html = """
    <tr class="tw-border-none">
      <td><p class="tw-text-gray-500">x</p></td>
    </tr>
    """
    soup = BeautifulSoup(html, 'html.parser')
    row = soup.find('tr')
    entry = {'comments': None}
    parse_additional_row(row, entry)
    assert entry['comments'] is None


# --- clean_text helper ---

@pytest.mark.web
def test_clean_text_strips_html():
    """clean_text removes HTML tags."""
    assert clean_text('<b>Hello</b> world') == 'Hello world'


@pytest.mark.web
def test_clean_text_none():
    """clean_text returns None for falsy input."""
    assert clean_text(None) is None
    assert clean_text('') is None
    assert clean_text('   ') is None


# --- File I/O ---

@pytest.mark.web
def test_save_and_load_data(tmp_path):
    """save_data writes JSON; load_data reads it back."""
    fp = str(tmp_path / 'test.json')
    data = [{'a': 1}]
    save_data(data, fp)
    loaded = load_data(fp)
    assert loaded == data


@pytest.mark.web
def test_load_data_missing_file():
    """load_data returns [] for non-existent file."""
    assert load_data('/no/such/file.json') == []


@pytest.mark.web
def test_save_data_creates_directory(tmp_path):
    """save_data creates parent directories if needed."""
    fp = str(tmp_path / 'sub' / 'dir' / 'data.json')
    save_data([1, 2], fp)
    assert load_data(fp) == [1, 2]


# --- scrape_data with mocked network ---

@pytest.mark.web
def test_scrape_data_success(monkeypatch):
    """First page has data, second page is empty -> should get 1 entry."""
    monkeypatch.setattr('src.scrape.time.sleep', lambda _: None)

    class FakeResp:
        """Minimal file-like that urlopen returns."""
        def __init__(self, html):
            self._html = html
        def read(self):
            return self._html.encode()
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass

    call_count = {'n': 0}
    def fake_urlopen(req, timeout=15):
        call_count['n'] += 1
        if call_count['n'] > 1:
            return FakeResp(EMPTY_HTML)   # empty page stops the loop
        return FakeResp(FAKE_HTML)

    monkeypatch.setattr('src.scrape.urlopen', fake_urlopen)
    data = scrape_data(num_pages=2, delay=0)
    assert len(data) == 1


@pytest.mark.web
def test_scrape_data_http_404_stops(monkeypatch):
    """A 404 means there are no more pages; scraper should stop."""
    monkeypatch.setattr('src.scrape.time.sleep', lambda _: None)

    def fake_urlopen(req, timeout=15):
        raise HTTPError(
            'http://x', 404, 'Not Found', {}, None
        )

    monkeypatch.setattr('src.scrape.urlopen', fake_urlopen)
    data = scrape_data(num_pages=3, delay=0)
    assert data == []


@pytest.mark.web
def test_scrape_data_http_500_retries(monkeypatch):
    """Server errors should be retried; after 5 in a row, give up."""
    monkeypatch.setattr('src.scrape.time.sleep', lambda _: None)

    def fake_urlopen(req, timeout=15):
        raise HTTPError(
            'http://x', 500, 'Server Error', {}, None
        )

    monkeypatch.setattr('src.scrape.urlopen', fake_urlopen)
    data = scrape_data(num_pages=10, delay=0)
    assert data == []


@pytest.mark.web
def test_scrape_data_url_error(monkeypatch):
    """Network errors (URLError) should also be handled gracefully."""
    monkeypatch.setattr('src.scrape.time.sleep', lambda _: None)

    def fake_urlopen(req, timeout=15):
        raise URLError('Connection refused')

    monkeypatch.setattr('src.scrape.urlopen', fake_urlopen)
    data = scrape_data(num_pages=10, delay=0)
    assert data == []


@pytest.mark.web
def test_scrape_data_generic_exception(monkeypatch):
    """Random exceptions shouldn't crash the whole scraper."""
    monkeypatch.setattr('src.scrape.time.sleep', lambda _: None)

    def fake_urlopen(req, timeout=15):
        raise RuntimeError('boom')

    monkeypatch.setattr('src.scrape.urlopen', fake_urlopen)
    data = scrape_data(num_pages=10, delay=0)
    assert data == []


@pytest.mark.web
def test_scrape_data_with_decision_filter(monkeypatch):
    """Passing result_type='accepted' should add a decision param to the URL."""
    monkeypatch.setattr('src.scrape.time.sleep', lambda _: None)

    class FakeResp:
        def __init__(self):
            pass
        def read(self):
            return EMPTY_HTML.encode()
        def __enter__(self):
            return self
        def __exit__(self, *a):
            pass

    monkeypatch.setattr(
        'src.scrape.urlopen', lambda req, timeout=15: FakeResp()
    )
    data = scrape_data(result_type='accepted', num_pages=1, delay=0)
    assert data == []
