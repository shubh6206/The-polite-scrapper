"""
Normalizer Module - Converts raw scraped strings into clean, deterministic data types.
FlyRank Backend Track Week 5 Assignment A9
"""

import re
from typing import Any, Dict


def normalize_price(price_text: str) -> float:
    """
    Normalizes raw price text (e.g. '£51.77', '51.77', '  £ 19.99  ') into a float.
    Raises ValueError if price_text does not contain a valid non-negative number.
    """
    if not price_text:
        raise ValueError("Price text is empty or missing")

    # Match numeric pattern with optional decimal part
    match = re.search(r"(\d+(?:\.\d+)?)", price_text.strip())
    if not match:
        raise ValueError(f"Could not extract numeric price from: '{price_text}'")

    try:
        price_val = float(match.group(1))
        if price_val < 0:
            raise ValueError(f"Price cannot be negative: {price_val}")
        return round(price_val, 2)
    except Exception as e:
        raise ValueError(f"Failed to parse price float from '{price_text}': {e}") from e


def normalize_url(url: str) -> str:
    """
    Ensures product URL is an absolute HTTPS URL.
    Converts http://books.toscrape.com to https://books.toscrape.com.
    """
    if not url:
        return ""
    clean_url = url.strip()
    if clean_url.startswith("http://books.toscrape.com"):
        clean_url = "https://" + clean_url[len("http://") :]
    return clean_url


def normalize_raw_record(raw_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms a raw 8-field dictionary into a normalized dictionary ready for schema validation.
    Computes 'price_gbp' while preserving original 'price_text'.
    """
    normalized = dict(raw_record)

    # 1. Price normalization
    raw_price = str(raw_record.get("price_text", ""))
    normalized["price_gbp"] = normalize_price(raw_price)

    # 2. URL canonicalization
    raw_url = str(raw_record.get("product_url", ""))
    normalized["product_url"] = normalize_url(raw_url)

    # 3. Clean string whitespace
    if isinstance(normalized.get("title"), str):
        normalized["title"] = normalized["title"].strip()
    if isinstance(normalized.get("availability_text"), str):
        normalized["availability_text"] = normalized["availability_text"].strip()
    if isinstance(normalized.get("rating_text"), str):
        normalized["rating_text"] = normalized["rating_text"].strip()
    if isinstance(normalized.get("description"), str):
        normalized["description"] = normalized["description"].strip() or None

    return normalized
