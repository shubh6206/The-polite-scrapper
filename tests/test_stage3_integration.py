"""
Integration test for Stage 3: Extract Book Details across all 60 books
"""

import http.server
import socketserver
import threading
import tempfile
import shutil
import unittest
from pathlib import Path

from src.fetcher import PoliteFetcher
from src.main import discover_catalogue_books, extract_all_book_details
from tests.test_urls import generate_mock_catalogue_html


def generate_mock_detail_html(book_id: int) -> str:
    has_desc = (book_id % 5 != 0)  # Some books without description
    desc_html = ""
    if has_desc:
        desc_html = f"""
        <div id="product_description" class="sub-heading"><h2>Product Description</h2></div>
        <p>This is the detailed description for Book number {book_id}.</p>
        """
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Book {book_id}</title></head>
    <body>
        <div class="product_main">
            <h1>Book Title {book_id}</h1>
            <p class="price_color">£{20.00 + book_id * 0.5:.2f}</p>
            <p class="instock availability">In stock ({book_id % 15 + 1} available)</p>
            <p class="star-rating Four"></p>
        </div>
        {desc_html}
    </body>
    </html>
    """


class MockFullSiteHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/catalogue/page-1.html":
            content = generate_mock_catalogue_html(1, has_next=True).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/catalogue/page-2.html":
            content = generate_mock_catalogue_html(2, has_next=True).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content)
        elif self.path == "/catalogue/page-3.html":
            content = generate_mock_catalogue_html(3, has_next=True).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content)
        elif "/book-" in self.path:
            import re
            m = re.search(r"book-(\d+)", self.path)
            book_id = int(m.group(1)) if m else 1
            content = generate_mock_detail_html(book_id).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


class TestStage3FullRun(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = socketserver.TCPServer(("127.0.0.1", 0), MockFullSiteHandler)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_full_stage_3_extraction(self):
        """Verify discovering 60 books and extracting all 8 raw fields for all 60 detail pages."""
        cache_dir = Path(self.temp_dir)
        books_cache = cache_dir / "books"
        fetcher = PoliteFetcher(timeout=5, min_delay=0.001)

        start_url = f"{self.base_url}/catalogue/page-1.html"
        book_items = discover_catalogue_books(
            fetcher=fetcher,
            start_url=start_url,
            max_pages=3,
            cache_dir=cache_dir,
        )
        self.assertEqual(len(book_items), 60)

        raw_records = extract_all_book_details(
            fetcher=fetcher,
            book_items=book_items,
            books_cache_dir=books_cache,
        )

        self.assertEqual(len(raw_records), 60)
        for record in raw_records:
            self.assertEqual(len(record), 8)
            self.assertTrue(record["title"])
            self.assertTrue(record["product_url"].startswith("http"))
            self.assertTrue(record["price_text"].startswith("£"))
            self.assertTrue(record["availability_text"])
            self.assertTrue(record["rating_text"])
            self.assertTrue(record["source_page"].startswith("http"))
            self.assertTrue(record["fetched_at"])
            # Check description is string or None
            self.assertTrue(record["description"] is None or isinstance(record["description"], str))


if __name__ == "__main__":
    unittest.main()
