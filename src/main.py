"""
The Polite Scraper - Main Pipeline
FlyRank Backend Track Week 5 Assignment A9
Stage 3: Extract Book Details
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from src.fetcher import PoliteFetcher, FetchError
from src.parser import (
    extract_catalogue_book_urls,
    extract_next_page_url,
    extract_book_details,
)

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
BOOKS_CACHE_DIR = CACHE_DIR / "books"
OUTPUT_DIR = BASE_DIR / "output"

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
MAX_CATALOGUE_PAGES = 3


def url_to_cache_filename(url: str) -> str:
    """Converts a book URL to a safe, readable cache filename."""
    path_parts = [p for p in urlparse(url).path.split("/") if p and p != "index.html"]
    slug = path_parts[-1] if path_parts else "unknown_book"
    # Ensure safe filename
    safe_slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", slug)
    return f"{safe_slug}.html"


def discover_catalogue_books(
    fetcher: PoliteFetcher,
    start_url: str = START_URL,
    max_pages: int = MAX_CATALOGUE_PAGES,
    cache_dir: Path = CACHE_DIR,
) -> List[Tuple[str, str]]:
    """
    Discovers book URLs from the first max_pages catalogue pages.
    Returns: List of tuples (product_url, source_catalogue_page_url)
    """
    current_url = start_url
    pages_visited = 0
    discovered: List[Tuple[str, str]] = []

    print("=" * 60)
    print(f"Catalogue Discovery (Limit: {max_pages} pages)")
    print("=" * 60)

    while current_url and pages_visited < max_pages:
        page_num = pages_visited + 1
        cache_file = cache_dir / f"catalogue-page-{page_num}.html"

        print(f"\n[Catalogue {page_num}/{max_pages}] {current_url}")
        html, from_cache, size_bytes = fetcher.fetch(current_url, cache_path=cache_file)
        pages_visited += 1

        page_books = extract_catalogue_book_urls(html, current_url)
        print(f"-> Found {len(page_books)} books on page {page_num}")
        for book_url in page_books:
            discovered.append((book_url, current_url))

        if pages_visited < max_pages:
            next_url = extract_next_page_url(html, current_url)
            if next_url:
                current_url = next_url
            else:
                break
        else:
            break

    # Deduplicate while preserving discovery order
    seen = set()
    unique_books: List[Tuple[str, str]] = []
    for book_url, source_url in discovered:
        if book_url not in seen:
            seen.add(book_url)
            unique_books.append((book_url, source_url))

    return unique_books


def extract_all_book_details(
    fetcher: PoliteFetcher,
    book_items: List[Tuple[str, str]],
    books_cache_dir: Path = BOOKS_CACHE_DIR,
) -> List[Dict[str, Any]]:
    """
    Fetches and extracts raw records for all discovered book detail pages.
    """
    books_cache_dir.mkdir(parents=True, exist_ok=True)
    raw_records: List[Dict[str, Any]] = []

    print("\n" + "=" * 60)
    print(f"Extracting details for {len(book_items)} books...")
    print("=" * 60)

    for idx, (book_url, source_page) in enumerate(book_items, 1):
        filename = url_to_cache_filename(book_url)
        cache_file = books_cache_dir / filename

        fetched_at = datetime.now(timezone.utc).isoformat()
        print(f"[{idx}/{len(book_items)}] Fetching detail: {book_url}")
        html, from_cache, size_bytes = fetcher.fetch(book_url, cache_path=cache_file)

        raw_record = extract_book_details(
            html=html,
            product_url=book_url,
            source_page=source_page,
            fetched_at=fetched_at,
        )
        raw_records.append(raw_record)

    return raw_records


def run_stage_3() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    BOOKS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fetcher = PoliteFetcher()

    try:
        # 1. Discover catalogue books
        book_items = discover_catalogue_books(fetcher)
        print(f"\nDiscovered {len(book_items)} unique book URLs.")

        # 2. Extract details
        raw_records = extract_all_book_details(fetcher, book_items)

        # 3. Print Checkpoint Results
        print("\n" + "=" * 60)
        print("STAGE 3 CHECKPOINT RESULT:")
        print(f"detail_pages={len(raw_records)}")
        print("=" * 60)

        if raw_records:
            print("\nSample Raw Record (Complete 8 fields):")
            print(json.dumps(raw_records[0], indent=2, ensure_ascii=False))

    except FetchError as e:
        print(f"[ERROR] Stage 3 failed: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    run_stage_3()


if __name__ == "__main__":
    main()
