"""
Reporter Module - Generates honest operational execution reports.
FlyRank Backend Track Week 5 Assignment A9
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class RunReporter:
    """
    Tracks runtime operational metrics for the scraper run.
    """

    def __init__(self):
        self.start_time = datetime.now(timezone.utc).isoformat()
        self._start_timestamp = time.time()
        self.catalogue_pages = 0
        self.discovered_urls = 0
        self.unique_urls = 0
        self.pages_fetched = 0
        self.cache_hits = 0
        self.valid_records = 0
        self.invalid_records = 0
        self.failed_pages = 0
        self.failed_urls: List[Dict[str, Any]] = []

    def record_cache_hit(self) -> None:
        self.cache_hits += 1

    def record_page_fetched(self) -> None:
        self.pages_fetched += 1

    def record_failed_page(self, url: str, reason: str, status_code: Optional[int] = None) -> None:
        self.failed_pages += 1
        self.failed_urls.append({
            "url": url,
            "reason": reason,
            "status_code": status_code,
            "failed_at": datetime.now(timezone.utc).isoformat(),
        })

    def generate_report(self) -> Dict[str, Any]:
        duration = round(time.time() - self._start_timestamp, 3)
        return {
            "start_time": self.start_time,
            "duration_seconds": duration,
            "catalogue_pages": self.catalogue_pages,
            "discovered_urls": self.discovered_urls,
            "unique_urls": self.unique_urls,
            "pages_fetched": self.pages_fetched,
            "cache_hits": self.cache_hits,
            "valid_records": self.valid_records,
            "invalid_records": self.invalid_records,
            "failed_pages": self.failed_pages,
            "failed_urls": self.failed_urls,
        }

    def save_report(self, output_path: Path) -> Dict[str, Any]:
        report = self.generate_report()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return report
