"""
Fetcher Module - Polite HTTP client with local caching and rate-limiting.
FlyRank Backend Track Week 5 Assignment A9
"""

import os
import time
from pathlib import Path
from typing import Optional, Tuple
import requests

# Politeness configuration constants
DEFAULT_USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/shubh6206/The-polite-scrapper)"
DEFAULT_TIMEOUT_SECONDS = 10
MIN_REQUEST_DELAY_SECONDS = 0.5  # 500 ms minimum delay between real HTTP requests


class FetchError(Exception):
    """Exception raised when an HTTP fetch fails."""
    def __init__(self, message: str, status_code: Optional[int] = None, url: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class PoliteFetcher:
    """
    Polite HTTP Fetcher that enforces:
    - Identifying User-Agent
    - Explicit request timeout
    - Status code validation (HTTP 200 only)
    - Minimum 500ms delay between consecutive live requests (no delay on cache hits)
    - Local disk caching
    """

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        min_delay: float = MIN_REQUEST_DELAY_SECONDS,
    ):
        self.user_agent = user_agent
        self.timeout = timeout
        self.min_delay = min_delay
        self._last_request_time: float = 0.0

    def _apply_delay(self) -> None:
        """Enforces minimum delay between real outbound requests."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self._last_request_time = time.time()

    def fetch(
        self,
        url: str,
        cache_path: Optional[Path] = None,
        force_refresh: bool = False,
    ) -> Tuple[str, bool, int]:
        """
        Fetches HTML from cache if available, otherwise performs a polite HTTP request.

        Returns:
            Tuple[html_content (str), from_cache (bool), size_bytes (int)]
        """
        # 1. Check local cache
        if cache_path and cache_path.exists() and not force_refresh:
            try:
                html = cache_path.read_text(encoding="utf-8")
                size = len(html.encode("utf-8"))
                print(f"[CACHE HIT] {url} ({size:,} bytes from {cache_path.name})")
                return html, True, size
            except Exception as e:
                print(f"[CACHE READ ERROR] Failed to read {cache_path}: {e}. Falling back to fetch.")

        # 2. Politeness delay before real request
        self._apply_delay()

        # 3. Perform live HTTP GET
        headers = {"User-Agent": self.user_agent}
        try:
            response = requests.get(url, headers=headers, timeout=self.timeout)
        except requests.exceptions.Timeout as e:
            raise FetchError(f"Request timed out after {self.timeout}s for URL: {url}", url=url) from e
        except requests.exceptions.RequestException as e:
            raise FetchError(f"HTTP request error for URL {url}: {e}", url=url) from e

        # 4. Status code validation (only 200 is acceptable)
        if response.status_code != 200:
            raise FetchError(
                f"Unexpected status code {response.status_code} for URL: {url}",
                status_code=response.status_code,
                url=url,
            )

        html = response.text
        size = len(response.content)
        print(f"[FETCH] {url} -> HTTP {response.status_code} ({size:,} bytes)")

        # 5. Cache response to disk
        if cache_path:
            try:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(html, encoding="utf-8")
            except Exception as e:
                print(f"[CACHE WRITE ERROR] Could not write cache to {cache_path}: {e}")

        return html, False, size
