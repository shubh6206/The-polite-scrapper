"""
Fetcher Module - Polite HTTP client with local caching, rate-limiting, and resilient retry rules.
FlyRank Backend Track Week 5 Assignment A9
"""

import os
import time
from pathlib import Path
from typing import Optional, Tuple
import requests

DEFAULT_USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/shubh6206/The-polite-scrapper)"
DEFAULT_TIMEOUT_SECONDS = 10
MIN_REQUEST_DELAY_SECONDS = 0.5
DEFAULT_RETRY_DELAY_SECONDS = 1.0


class FetchError(Exception):
    """Exception raised when an HTTP fetch fails."""
    def __init__(self, message: str, status_code: Optional[int] = None, url: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.url = url


class PoliteFetcher:
    """
    Polite HTTP Fetcher enforcing:
    - Identifying User-Agent
    - Finite timeout per request
    - Status code checking (HTTP 200 required)
    - Minimum 500ms delay between consecutive live requests
    - Local disk caching
    - Resilient retry rules:
        * 403 / 404: Never retried
        * Timeout / 5xx: Retried exactly once after a brief pause
    """

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
        min_delay: float = MIN_REQUEST_DELAY_SECONDS,
        retry_delay: float = DEFAULT_RETRY_DELAY_SECONDS,
    ):
        self.user_agent = user_agent
        self.timeout = timeout
        self.min_delay = min_delay
        self.retry_delay = retry_delay
        self._last_request_time: float = 0.0

    def _apply_delay(self) -> None:
        """Enforces rate limiting between live requests."""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self.min_delay:
            time.sleep(self.min_delay - elapsed)
        self._last_request_time = time.time()

    def _execute_single_fetch(self, url: str) -> requests.Response:
        """Executes a single HTTP GET request with timeout and user agent."""
        self._apply_delay()
        headers = {"User-Agent": self.user_agent}
        return requests.get(url, headers=headers, timeout=self.timeout)

    def fetch(
        self,
        url: str,
        cache_path: Optional[Path] = None,
        force_refresh: bool = False,
        retry_on_failure: bool = True,
    ) -> Tuple[str, bool, int]:
        """
        Fetches a URL, reading from cache if available or performing live HTTP GET with retry.

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
                print(f"[CACHE READ ERROR] Failed to read {cache_path}: {e}")

        # 2. First HTTP Attempt
        attempt = 1
        max_attempts = 2 if retry_on_failure else 1

        while attempt <= max_attempts:
            try:
                response = self._execute_single_fetch(url)

                # HTTP 200 is success
                if response.status_code == 200:
                    html = response.text
                    size = len(response.content)
                    print(f"[FETCH] {url} -> HTTP 200 ({size:,} bytes, attempt {attempt})")

                    if cache_path:
                        try:
                            cache_path.parent.mkdir(parents=True, exist_ok=True)
                            cache_path.write_text(html, encoding="utf-8")
                        except Exception as e:
                            print(f"[CACHE WRITE ERROR] {e}")

                    return html, False, size

                # Non-200 responses
                status = response.status_code

                # Rule: DO NOT retry 403 or 404
                if status in (403, 404):
                    print(f"[HTTP {status}] Client refusal/not found for {url} - DO NOT RETRY")
                    raise FetchError(f"HTTP {status} for URL {url}", status_code=status, url=url)

                # Rule: 5xx server errors retry once
                if 500 <= status < 600:
                    if attempt < max_attempts:
                        print(f"[HTTP {status}] Server error for {url} - Retrying once after {self.retry_delay}s...")
                        time.sleep(self.retry_delay)
                        attempt += 1
                        continue
                    else:
                        raise FetchError(f"HTTP {status} server error persisted after retry for URL: {url}", status_code=status, url=url)

                # Other unexpected statuses
                raise FetchError(f"Unexpected status HTTP {status} for URL: {url}", status_code=status, url=url)

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                # Rule: Timeouts and connection errors retry once
                if attempt < max_attempts:
                    print(f"[TIMEOUT/ERROR] {e} for {url} - Retrying once after {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                    attempt += 1
                    continue
                else:
                    raise FetchError(f"Request failed after retry for URL: {url} ({e})", url=url) from e
            except FetchError:
                raise
            except Exception as e:
                raise FetchError(f"Fatal request exception for URL {url}: {e}", url=url) from e

        raise FetchError(f"Exhausted attempts for URL: {url}", url=url)
