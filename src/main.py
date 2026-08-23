"""
The Polite Scraper - Main Pipeline
FlyRank Backend Track Week 5 Assignment A9
Stage 2: Discover Three Catalogue Pages
"""

import sys
from pathlib import Path
from typing import List, Tuple

from src.fetcher import PoliteFetcher, FetchError
from src.parser import extract_catalogue_book_urls, extract_next_page_url

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
OUTPUT_DIR = BASE_DIR / "output"

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
MAX_CATALOGUE_PAGES = 3


def discover_catalogue_books(
    fetcher: PoliteFetcher,
    start_url: str = START_URL,
    max_pages: int = MAX_CATALOGUE_PAGES,
    cache_dir: Path = CACHE_DIR,
) -> Tuple[int, int, List[str]]:
    """
    Discovers book URLs by navigating up to max_pages catalogue pages.
    Returns:
        Tuple[catalogue_pages_visited (int), total_discovered (int), unique_urls (List[str])]
    """
    current_url = start_url
    pages_visited = 0
    discovered_urls: List[str] = []

    print("=" * 60)
    print(f"Starting catalogue discovery (Limit: {max_pages} pages)")
    print("=" * 60)

    while current_url and pages_visited < max_pages:
        page_num = pages_visited + 1
        cache_file = cache_dir / f"catalogue-page-{page_num}.html"

        print(f"\n[Catalogue Page {page_num}/{max_pages}] Processing: {current_url}")
        html, from_cache, size_bytes = fetcher.fetch(current_url, cache_path=cache_file)
        pages_visited += 1

        page_books = extract_catalogue_book_urls(html, current_url)
        print(f"-> Discovered {len(page_books)} books on page {page_num}")
        discovered_urls.extend(page_books)

        if pages_visited < max_pages:
            next_url = extract_next_page_url(html, current_url)
            if next_url:
                current_url = next_url
            else:
                print("-> No next page link found. Stopping pagination.")
                break
        else:
            print(f"-> Reached maximum catalogue limit ({max_pages} pages). Stopping pagination.")
            break

    # Deduplicate while preserving discovery order
    seen = set()
    unique_urls: List[str] = []
    for url in discovered_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return pages_visited, len(discovered_urls), unique_urls


def run_stage_2() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    fetcher = PoliteFetcher()

    try:
        pages_count, discovered_count, unique_urls = discover_catalogue_books(
            fetcher=fetcher,
            start_url=START_URL,
            max_pages=MAX_CATALOGUE_PAGES,
            cache_dir=CACHE_DIR,
        )

        print("\n" + "=" * 60)
        print("STAGE 2 CHECKPOINT RESULT:")
        print(f"catalogue_pages={pages_count}")
        print(f"discovered={discovered_count}")
        print(f"unique_urls={len(unique_urls)}")
        print("=" * 60)

        # Print a small sample of discovered URLs for verification
        if unique_urls:
            print("\nSample discovered URLs (first 3):")
            for i, u in enumerate(unique_urls[:3], 1):
                print(f"  {i}. {u}")
            print(f"  ... ({len(unique_urls) - 3} more URLs)")

    except FetchError as e:
        print(f"[ERROR] Stage 2 failed: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    run_stage_2()


if __name__ == "__main__":
    main()
