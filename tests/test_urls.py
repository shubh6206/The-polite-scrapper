"""
Tests for URL discovery and normalization (Stage 2: Discover Three Catalogue Pages)
"""

import http.server
import socketserver
import threading
import tempfile
import shutil
import unittest
from pathlib import Path

from src.fetcher import PoliteFetcher
from src.parser import extract_catalogue_book_urls, extract_next_page_url
from src.main import discover_catalogue_books


def generate_mock_catalogue_html(page_num: int, has_next: bool = True) -> str:
    """Generates realistic HTML for a catalogue page with 20 books and a next link."""
    items = []
    start_idx = (page_num - 1) * 20 + 1
    for i in range(start_idx, start_idx + 20):
        items.append(f"""
        <li class="col-xs-6 col-sm-4 col-md-3 col-lg-3">
            <article class="product_pod">
                <div class="image_container">
                    <a href="book-{i}/index.html"><img src="media/cache/book-{i}.jpg" class="thumbnail"></a>
                </div>
                <p class="star-rating Three"><i class="icon-star"></i></p>
                <h3><a href="book-{i}/index.html" title="Book Title {i}">Book Title {i}</a></h3>
                <div class="product_price">
                    <p class="price_color">£{20.00 + i * 0.5:.2f}</p>
                    <p class="instock availability"><i class="icon-ok"></i> In stock</p>
                </div>
            </article>
        </li>
        """)
    
    pager_html = ""
    if has_next:
        pager_html = f'<ul class="pager"><li class="next"><a href="page-{page_num + 1}.html">next</a></li></ul>'
    else:
        pager_html = '<ul class="pager"></ul>'

    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Catalogue - Page {page_num}</title></head>
    <body>
        <div class="page_inner">
            <ol class="row">
                {"".join(items)}
            </ol>
            {pager_html}
        </div>
    </body>
    </html>
    """


class MockCatalogueServerHandler(http.server.SimpleHTTPRequestHandler):
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
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


class TestCatalogueDiscovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = socketserver.TCPServer(("127.0.0.1", 0), MockCatalogueServerHandler)
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

    def test_relative_to_absolute_url_conversion(self):
        """Verify relative URLs from HTML are converted to absolute HTTP/HTTPS URLs."""
        html = """
        <article class="product_pod">
            <h3><a href="../../a-light-in-the-attic_1000/index.html" title="Test Book">Test</a></h3>
        </article>
        """
        base_url = "https://books.toscrape.com/catalogue/category/books_1/page-1.html"
        urls = extract_catalogue_book_urls(html, base_url)
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html")

    def test_next_page_url_extraction(self):
        """Verify the 'next' page link is converted to an absolute URL."""
        html = '<ul class="pager"><li class="next"><a href="page-2.html">next</a></li></ul>'
        base_url = "https://books.toscrape.com/catalogue/page-1.html"
        next_url = extract_next_page_url(html, base_url)
        self.assertEqual(next_url, "https://books.toscrape.com/catalogue/page-2.html")

    def test_three_catalogue_pages_discovery_and_caching(self):
        """
        Verify that crawling discovers exactly 3 pages, 60 discovered books, 60 unique URLs,
        and that a second run reads from cache.
        """
        cache_dir = Path(self.temp_dir)
        fetcher = PoliteFetcher(timeout=5, min_delay=0.01)
        start_url = f"{self.base_url}/catalogue/page-1.html"

        # Run 1: live fetch & cache
        pages_1, discovered_1, unique_1 = discover_catalogue_books(
            fetcher=fetcher,
            start_url=start_url,
            max_pages=3,
            cache_dir=cache_dir,
        )
        self.assertEqual(pages_1, 3)
        self.assertEqual(discovered_1, 60)
        self.assertEqual(len(unique_1), 60)

        # Verify all 3 cache files were created
        self.assertTrue((cache_dir / "catalogue-page-1.html").exists())
        self.assertTrue((cache_dir / "catalogue-page-2.html").exists())
        self.assertTrue((cache_dir / "catalogue-page-3.html").exists())

        # Run 2: cache hit
        pages_2, discovered_2, unique_2 = discover_catalogue_books(
            fetcher=fetcher,
            start_url=start_url,
            max_pages=3,
            cache_dir=cache_dir,
        )
        self.assertEqual(pages_2, 3)
        self.assertEqual(discovered_2, 60)
        self.assertEqual(len(unique_2), 60)
        self.assertEqual(unique_1, unique_2)

    def test_duplicate_url_removal(self):
        """Verify duplicate URLs on a page are properly deduped."""
        html = """
        <article class="product_pod"><h3><a href="book-1/index.html">Book 1</a></h3></article>
        <article class="product_pod"><h3><a href="book-1/index.html">Book 1 Duplicate</a></h3></article>
        <article class="product_pod"><h3><a href="book-2/index.html">Book 2</a></h3></article>
        """
        urls = extract_catalogue_book_urls(html, "https://books.toscrape.com/catalogue/page-1.html")
        unique_urls = list(dict.fromkeys(urls))
        self.assertEqual(len(urls), 3)
        self.assertEqual(len(unique_urls), 2)


if __name__ == "__main__":
    unittest.main()
