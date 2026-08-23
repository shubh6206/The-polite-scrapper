"""
Unit Tests for Duplicate URL and Idempotency Handling (Test 4 of Required 5)
"""

import unittest
from src.main import normalize_and_validate_records


class TestDuplicatesAndIdempotency(unittest.TestCase):
    def test_duplicate_product_urls_deduplicated(self):
        """Verify identical product URLs produce only 1 stored record."""
        raw_records = [
            {
                "title": "A Light in the Attic",
                "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                "price_text": "£51.77",
                "availability_text": "In stock (22 available)",
                "rating_text": "Three",
                "description": "A wonderful book.",
                "source_page": "https://books.toscrape.com/catalogue/page-1.html",
                "fetched_at": "2026-08-23T12:00:00Z",
            },
            {
                "title": "A Light in the Attic (Duplicate)",
                "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
                "price_text": "£51.77",
                "availability_text": "In stock (22 available)",
                "rating_text": "Three",
                "description": "A wonderful book duplicate.",
                "source_page": "https://books.toscrape.com/catalogue/page-2.html",
                "fetched_at": "2026-08-23T12:01:00Z",
            },
            {
                "title": "Tipping the Velvet",
                "product_url": "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html",
                "price_text": "£53.74",
                "availability_text": "In stock (20 available)",
                "rating_text": "One",
                "description": "Historical novel.",
                "source_page": "https://books.toscrape.com/catalogue/page-1.html",
                "fetched_at": "2026-08-23T12:00:00Z",
            },
        ]

        valid, invalid = normalize_and_validate_records(raw_records)
        self.assertEqual(len(invalid), 0)
        self.assertEqual(len(valid), 2)
        urls = [r["product_url"] for r in valid]
        self.assertEqual(len(urls), len(set(urls)))

    def test_rerun_idempotency_keeps_exact_record_count(self):
        """Verify re-running validation over repeated datasets maintains exactly 60 records."""
        # Create 60 unique sample records
        sample_60 = []
        for i in range(1, 61):
            sample_60.append({
                "title": f"Book Title {i}",
                "product_url": f"https://books.toscrape.com/catalogue/book-{i}_100{i}/index.html",
                "price_text": f"£{20.00 + i * 0.5:.2f}",
                "availability_text": "In stock (10 available)",
                "rating_text": "Four",
                "description": f"Description {i}",
                "source_page": "https://books.toscrape.com/catalogue/page-1.html",
                "fetched_at": "2026-08-23T12:00:00Z",
            })

        # Run 1: 60 records
        valid_1, _ = normalize_and_validate_records(sample_60)
        self.assertEqual(len(valid_1), 60)

        # Run 2: doubled list of 120 records (simulating rerun over existing data)
        valid_2, _ = normalize_and_validate_records(sample_60 + sample_60)
        self.assertEqual(len(valid_2), 60)


if __name__ == "__main__":
    unittest.main()
