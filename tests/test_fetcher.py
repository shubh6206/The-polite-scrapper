"""
Tests for PoliteFetcher (Stage 1: Fetch and cache HTML)
"""

import http.server
import socketserver
import threading
import time
import unittest
from pathlib import Path
import tempfile
import shutil

from src.fetcher import PoliteFetcher, FetchError, DEFAULT_USER_AGENT


class MockServerHandler(http.server.SimpleHTTPRequestHandler):
    request_count = 0
    last_user_agent = None

    def do_GET(self):
        MockServerHandler.request_count += 1
        MockServerHandler.last_user_agent = self.headers.get("User-Agent")

        if self.path == "/catalogue/page-1.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Catalogue Page 1</h1></body></html>")
        elif self.path == "/error-404":
            self.send_response(404)
            self.end_headers()
        elif self.path == "/error-500":
            self.send_response(500)
            self.end_headers()
        else:
            self.send_response(400)
            self.end_headers()

    def log_message(self, format, *args):
        # Suppress standard HTTP server output during tests
        pass


class TestPoliteFetcher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start a local HTTP server on a random open port
        cls.server = socketserver.TCPServer(("127.0.0.1", 0), MockServerHandler)
        cls.port = cls.server.server_address[1]
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        MockServerHandler.request_count = 0
        MockServerHandler.last_user_agent = None
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_fetch_and_cache_lifecycle(self):
        """Verify first call fetches and caches; second call uses cache without network."""
        cache_path = Path(self.temp_dir) / "test-page-1.html"
        fetcher = PoliteFetcher(user_agent="TestAgent/1.0", timeout=5, min_delay=0.1)

        target_url = f"{self.base_url}/catalogue/page-1.html"

        # 1. First fetch (Cache miss -> Network fetch)
        html1, from_cache1, size1 = fetcher.fetch(target_url, cache_path=cache_path)
        self.assertFalse(from_cache1)
        self.assertIn("Catalogue Page 1", html1)
        self.assertTrue(cache_path.exists())
        self.assertEqual(MockServerHandler.request_count, 1)
        self.assertEqual(MockServerHandler.last_user_agent, "TestAgent/1.0")

        # 2. Second fetch (Cache hit -> Disk read, no network)
        html2, from_cache2, size2 = fetcher.fetch(target_url, cache_path=cache_path)
        self.assertTrue(from_cache2)
        self.assertEqual(html1, html2)
        self.assertEqual(size1, size2)
        self.assertEqual(MockServerHandler.request_count, 1)  # Request count must NOT increment

    def test_status_code_validation(self):
        """Verify non-200 responses raise FetchError."""
        fetcher = PoliteFetcher(min_delay=0.01)
        with self.assertRaises(FetchError) as ctx:
            fetcher.fetch(f"{self.base_url}/error-404")
        self.assertEqual(ctx.exception.status_code, 404)

        with self.assertRaises(FetchError) as ctx:
            fetcher.fetch(f"{self.base_url}/error-500")
        self.assertEqual(ctx.exception.status_code, 500)

    def test_polite_rate_limiting_delay(self):
        """Verify rate-limiting delay between consecutive live requests."""
        fetcher = PoliteFetcher(min_delay=0.3)
        target_url = f"{self.base_url}/catalogue/page-1.html"

        start_time = time.time()
        fetcher.fetch(target_url)  # First request
        fetcher.fetch(target_url)  # Second request (must be delayed by >= 0.3s)
        duration = time.time() - start_time
        self.assertGreaterEqual(duration, 0.3)


if __name__ == "__main__":
    unittest.main()
