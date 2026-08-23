"""
Tests for Detail Extraction and Missing Description Handling (Stage 3)
"""

import unittest
from src.parser import extract_book_details


class TestDetailExtraction(unittest.TestCase):
    def test_extract_complete_book_details(self):
        """Verify extraction of all 8 raw fields when description and full metadata exist."""
        html = """
        <!DOCTYPE html>
        <html>
        <body>
            <div class="product_main">
                <h1>A Light in the Attic</h1>
                <p class="price_color">£51.77</p>
                <p class="instock availability">
                    <i class="icon-ok"></i>
                    In stock (22 available)
                </p>
                <p class="star-rating Three">
                    <i class="icon-star"></i>
                    <i class="icon-star"></i>
                    <i class="icon-star"></i>
                </p>
            </div>
            <div id="product_description" class="sub-heading">
                <h2>Product Description</h2>
            </div>
            <p>It's hard to imagine a world without A Light in the Attic...</p>
        </body>
        </html>
        """
        product_url = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
        source_page = "https://books.toscrape.com/catalogue/page-1.html"
        fetched_at = "2026-08-23T12:00:00Z"

        record = extract_book_details(html, product_url, source_page, fetched_at)

        # Verify all 8 keys exist
        expected_keys = {
            "title",
            "product_url",
            "price_text",
            "availability_text",
            "rating_text",
            "description",
            "source_page",
            "fetched_at",
        }
        self.assertEqual(set(record.keys()), expected_keys)

        self.assertEqual(record["title"], "A Light in the Attic")
        self.assertEqual(record["product_url"], product_url)
        self.assertEqual(record["price_text"], "£51.77")
        self.assertEqual(record["availability_text"], "In stock (22 available)")
        self.assertEqual(record["rating_text"], "Three")
        self.assertEqual(
            record["description"],
            "It's hard to imagine a world without A Light in the Attic...",
        )
        self.assertEqual(record["source_page"], source_page)
        self.assertEqual(record["fetched_at"], fetched_at)

    def test_missing_description_becomes_none(self):
        """Verify that when product description is absent in HTML, description is explicitly None."""
        html = """
        <!DOCTYPE html>
        <html>
        <body>
            <div class="product_main">
                <h1>Alice in Wonderland</h1>
                <p class="price_color">£15.00</p>
                <p class="instock availability">In stock (5 available)</p>
                <p class="star-rating One"></p>
            </div>
            <!-- No #product_description div or paragraph -->
        </body>
        </html>
        """
        record = extract_book_details(
            html,
            "https://books.toscrape.com/catalogue/alice_1/index.html",
            "https://books.toscrape.com/catalogue/page-1.html",
            "2026-08-23T12:00:00Z",
        )
        self.assertEqual(record["title"], "Alice in Wonderland")
        self.assertIsNone(record["description"])
        self.assertEqual(len(record), 8)


if __name__ == "__main__":
    unittest.main()
