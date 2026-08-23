"""
Unit Tests for Malformed HTML Fixture Handling (Test 5 of Required 5)
"""

import unittest
from pathlib import Path
from src.parser import extract_book_details
from src.main import normalize_and_validate_records

FIXTURE_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "malformed.html"


class TestMalformedFixture(unittest.TestCase):
    def test_malformed_html_isolated_into_errors(self):
        """
        Verify that malformed HTML is safely parsed without crashing,
        fails schema validation cleanly, and is isolated to invalid_records.
        """
        self.assertTrue(FIXTURE_PATH.exists(), f"Fixture missing at {FIXTURE_PATH}")
        malformed_html = FIXTURE_PATH.read_text(encoding="utf-8")

        # 1. Parsing must not raise an unhandled exception
        raw_record = extract_book_details(
            html=malformed_html,
            product_url="https://books.toscrape.com/catalogue/broken-book_0/index.html",
            source_page="https://books.toscrape.com/catalogue/page-1.html",
            fetched_at="2026-08-23T12:00:00Z",
        )
        self.assertIsInstance(raw_record, dict)
        self.assertEqual(len(raw_record), 8)

        # 2. Validation must isolate the invalid record without crashing
        valid, invalid = normalize_and_validate_records([raw_record])
        self.assertEqual(len(valid), 0)
        self.assertEqual(len(invalid), 1)
        self.assertEqual(invalid[0]["raw_record"]["product_url"], "https://books.toscrape.com/catalogue/broken-book_0/index.html")
        self.assertTrue(invalid[0]["error_reason"])


if __name__ == "__main__":
    unittest.main()
