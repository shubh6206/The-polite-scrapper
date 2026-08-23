"""
The Polite Scraper - Main Pipeline
FlyRank Backend Track Week 5 Assignment A9
Stage 1: Fetch and cache HTML
"""

import sys
from pathlib import Path
from src.fetcher import PoliteFetcher, FetchError

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "output"
PAGE_1_URL = "https://books.toscrape.com/catalogue/page-1.html"


def run_stage_1() -> None:
    """Stage 1 Checkpoint: Fetch and cache catalogue page 1."""
    print("=" * 60)
    print("Stage 1: Fetch and Cache HTML")
    print(f"Target URL: {PAGE_1_URL}")
    print("=" * 60)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    cache_file = CACHE_DIR / "catalogue-page-1.html"
    fetcher = PoliteFetcher()

    try:
        html, from_cache, size_bytes = fetcher.fetch(PAGE_1_URL, cache_path=cache_file)
        status_label = "CACHE HIT" if from_cache else "FETCH (Live HTTP 200)"
        print("-" * 60)
        print(f"Result: {status_label}")
        print(f"Cache File: {cache_file.relative_to(BASE_DIR)}")
        print(f"Response Size: {size_bytes:,} bytes ({len(html):,} characters)")
        print(f"Full HTML suppressed: [Verified - {size_bytes:,} bytes stored cleanly]")
        print("-" * 60)
    except FetchError as e:
        print(f"[ERROR] Fetch failed: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    run_stage_1()


if __name__ == "__main__":
    main()
