"""
The Polite Scraper - Main Pipeline
FlyRank Backend Track Week 5 Assignment A9
Stage 5: Survive Failures and Generate Run Report
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from pydantic import ValidationError

from src.fetcher import PoliteFetcher, FetchError
from src.parser import (
    extract_catalogue_book_urls,
    extract_next_page_url,
    extract_book_details,
)
from src.normalizer import normalize_raw_record
from src.models import BookRecord, RecordValidationError
from src.reporter import RunReporter

BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
BOOKS_CACHE_DIR = CACHE_DIR / "books"
OUTPUT_DIR = BASE_DIR / "output"
BOOKS_JSON = OUTPUT_DIR / "books.json"
ERRORS_JSON = OUTPUT_DIR / "errors.json"
RUN_REPORT_JSON = OUTPUT_DIR / "run-report.json"

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
MAX_CATALOGUE_PAGES = 3


def url_to_cache_filename(url: str) -> str:
    """Converts a book URL to a safe, readable cache filename."""
    path_parts = [p for p in urlparse(url).path.split("/") if p and p != "index.html"]
    slug = path_parts[-1] if path_parts else "unknown_book"
    safe_slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", slug)
    return f"{safe_slug}.html"


def discover_catalogue_books(
    fetcher: PoliteFetcher,
    reporter: Optional[RunReporter] = None,
    start_url: str = START_URL,
    max_pages: int = MAX_CATALOGUE_PAGES,
    cache_dir: Path = CACHE_DIR,
) -> List[Tuple[str, str]]:
    """
    Discovers book URLs from the first max_pages catalogue pages.
    Returns: List of tuples (product_url, source_catalogue_page_url)
    """
    if reporter is None:
        reporter = RunReporter()

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
        try:
            html, from_cache, size_bytes = fetcher.fetch(current_url, cache_path=cache_file)
            if from_cache:
                reporter.record_cache_hit()
            else:
                reporter.record_page_fetched()
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
        except FetchError as e:
            print(f"[CATALOGUE ERROR] Failed to fetch catalogue page {current_url}: {e}")
            reporter.record_failed_page(url=current_url, reason=str(e), status_code=e.status_code)
            break

    reporter.catalogue_pages = pages_visited
    reporter.discovered_urls = len(discovered)

    seen = set()
    unique_books: List[Tuple[str, str]] = []
    for book_url, source_url in discovered:
        if book_url not in seen:
            seen.add(book_url)
            unique_books.append((book_url, source_url))

    reporter.unique_urls = len(unique_books)
    return unique_books


def extract_all_book_details(
    fetcher: PoliteFetcher,
    reporter: Optional[RunReporter] = None,
    book_items: Optional[List[Tuple[str, str]]] = None,
    books_cache_dir: Path = BOOKS_CACHE_DIR,
) -> List[Dict[str, Any]]:
    """
    Fetches and extracts raw records for all discovered book detail pages.
    Survives individual page failures and logs them into reporter.
    """
    if reporter is None:
        reporter = RunReporter()
    if book_items is None:
        book_items = []

    books_cache_dir.mkdir(parents=True, exist_ok=True)
    raw_records: List[Dict[str, Any]] = []

    print("\n" + "=" * 60)
    print(f"Extracting details for {len(book_items)} books...")
    print("=" * 60)

    for idx, (book_url, source_page) in enumerate(book_items, 1):
        filename = url_to_cache_filename(book_url)
        cache_file = books_cache_dir / filename

        print(f"[{idx}/{len(book_items)}] Detail: {book_url}")
        try:
            fetched_at = datetime.now(timezone.utc).isoformat()
            html, from_cache, size_bytes = fetcher.fetch(book_url, cache_path=cache_file)
            if from_cache:
                reporter.record_cache_hit()
            else:
                reporter.record_page_fetched()

            raw_record = extract_book_details(
                html=html,
                product_url=book_url,
                source_page=source_page,
                fetched_at=fetched_at,
            )
            raw_records.append(raw_record)

        except FetchError as e:
            print(f"[PAGE FAILURE] {book_url} failed: {e}. Skipping and continuing pipeline.")
            reporter.record_failed_page(url=book_url, reason=str(e), status_code=e.status_code)
            continue
        except Exception as e:
            print(f"[PARSING ERROR] {book_url} error: {e}. Skipping.")
            reporter.record_failed_page(url=book_url, reason=f"Parsing error: {e}")
            continue

    return raw_records


def normalize_and_validate_records(
    raw_records: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Normalizes raw records, deduplicates by canonical product URL, and validates against Pydantic schema.
    Returns: Tuple[valid_records (List[dict]), invalid_records (List[dict])]
    """
    valid_records_dict: Dict[str, Dict[str, Any]] = {}
    invalid_records: List[Dict[str, Any]] = []

    for raw in raw_records:
        try:
            normalized = normalize_raw_record(raw)
            validated_model = BookRecord(**normalized)
            record_dict = validated_model.dict()

            valid_records_dict[record_dict["product_url"]] = record_dict

        except (ValidationError, ValueError, Exception) as e:
            err = RecordValidationError(raw_record=raw, error_reason=str(e))
            invalid_records.append(err.dict())

    return list(valid_records_dict.values()), invalid_records


def save_pipeline_output(
    valid_records: List[Dict[str, Any]],
    invalid_records: List[Dict[str, Any]],
    reporter: RunReporter,
    output_dir: Path = OUTPUT_DIR,
) -> Dict[str, Any]:
    """Saves books.json, errors.json, and run-report.json."""
    output_dir.mkdir(parents=True, exist_ok=True)

    books_file = output_dir / "books.json"
    errors_file = output_dir / "errors.json"
    report_file = output_dir / "run-report.json"

    with open(books_file, "w", encoding="utf-8") as f:
        json.dump(valid_records, f, indent=2, ensure_ascii=False)

    with open(errors_file, "w", encoding="utf-8") as f:
        json.dump(invalid_records, f, indent=2, ensure_ascii=False)

    reporter.valid_records = len(valid_records)
    reporter.invalid_records = len(invalid_records)
    report_dict = reporter.save_report(report_file)

    print(f"\n[OUTPUT] Saved {len(valid_records)} records to {books_file.name}")
    print(f"[OUTPUT] Saved {len(invalid_records)} errors to {errors_file.name}")
    print(f"[OUTPUT] Saved run report to {report_file.name}")

    return report_dict


def run_pipeline(
    fetcher: Optional[PoliteFetcher] = None,
    start_url: str = START_URL,
    max_pages: int = MAX_CATALOGUE_PAGES,
    cache_dir: Path = CACHE_DIR,
    output_dir: Path = OUTPUT_DIR,
    injected_fake_url: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Executes the complete end-to-end scraper pipeline.
    """
    if fetcher is None:
        fetcher = PoliteFetcher()

    reporter = RunReporter()
    books_cache_dir = cache_dir / "books"

    # 1. Discover catalogue books
    book_items = discover_catalogue_books(
        fetcher=fetcher,
        reporter=reporter,
        start_url=start_url,
        max_pages=max_pages,
        cache_dir=cache_dir,
    )

    # Inject deliberate broken URL for failure testing if requested
    if injected_fake_url:
        print(f"\n[TESTING] Injecting fake broken URL for failure resilience test: {injected_fake_url}")
        book_items.append((injected_fake_url, start_url))

    # 2. Extract detail pages
    raw_records = extract_all_book_details(
        fetcher=fetcher,
        reporter=reporter,
        book_items=book_items,
        books_cache_dir=books_cache_dir,
    )

    # 3. Normalize & Validate
    valid_records, invalid_records = normalize_and_validate_records(raw_records)

    # 4. Save clean outputs and honest report
    report = save_pipeline_output(
        valid_records=valid_records,
        invalid_records=invalid_records,
        reporter=reporter,
        output_dir=output_dir,
    )

    return valid_records, invalid_records, report


def main() -> None:
    valid, invalid, report = run_pipeline()
    print("\n" + "=" * 60)
    print("STAGE 5 RUN REPORT SUMMARY:")
    print(json.dumps(report, indent=2))
    print("=" * 60)


if __name__ == "__main__":
    main()
