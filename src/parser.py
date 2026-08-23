"""
Parser Module - Extracts book links, pagination, and detail fields from HTML.
FlyRank Backend Track Week 5 Assignment A9
"""

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup


def extract_catalogue_book_urls(html: str, base_url: str) -> List[str]:
    """
    Parses a catalogue page HTML and extracts all book product URLs.
    Converts relative links to absolute URLs using urllib.parse.urljoin.
    """
    soup = BeautifulSoup(html, "html.parser")
    book_urls: List[str] = []

    product_pods = soup.select("article.product_pod")
    for pod in product_pods:
        title_anchor = pod.select_one("h3 > a")
        if title_anchor and title_anchor.get("href"):
            href = title_anchor["href"]
            abs_url = urljoin(base_url, href)
            book_urls.append(abs_url)

    return book_urls


def extract_next_page_url(html: str, base_url: str) -> Optional[str]:
    """
    Finds the 'next' pagination link on a catalogue page and returns its absolute URL.
    Returns None if no next link is present.
    """
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.select_one("li.next > a")
    if next_link and next_link.get("href"):
        return urljoin(base_url, next_link["href"])
    return None


def extract_book_details(
    html: str,
    product_url: str,
    source_page: str,
    fetched_at: str,
) -> Dict[str, Any]:
    """
    Extracts the eight required raw fields from a book detail page HTML:
    - title (str)
    - product_url (str)
    - price_text (str)
    - availability_text (str)
    - rating_text (str)
    - description (Optional[str]) - None if missing
    - source_page (str) - provenance
    - fetched_at (str) - provenance (ISO 8601 timestamp)
    """
    soup = BeautifulSoup(html, "html.parser")

    # 1. Product area selector
    product_main = soup.select_one("div.product_main") or soup.select_one("article.product_page")

    # 2. Title
    title_elem = product_main.select_one("h1") if product_main else soup.select_one("h1")
    title = title_elem.get_text(strip=True) if title_elem else ""

    # 3. Price text
    price_elem = product_main.select_one("p.price_color") if product_main else soup.select_one("p.price_color")
    price_text = price_elem.get_text(strip=True) if price_elem else ""

    # 4. Availability text
    avail_elem = (
        product_main.select_one("p.instock.availability")
        if product_main
        else soup.select_one("p.instock.availability")
    )
    if avail_elem:
        # Clean extra internal spaces/newlines e.g. "In stock (22 available)"
        avail_text = " ".join(avail_elem.get_text().split())
    else:
        avail_text = ""

    # 5. Rating text
    rating_text = ""
    rating_elem = (
        product_main.select_one("p.star-rating")
        if product_main
        else soup.select_one("p.star-rating")
    )
    if rating_elem and rating_elem.get("class"):
        classes = [c for c in rating_elem["class"] if c != "star-rating"]
        if classes:
            rating_text = classes[0]

    # 6. Description (located after #product_description header)
    description = None
    desc_header = soup.select_one("#product_description")
    if desc_header:
        # The description paragraph immediately follows the #product_description div
        desc_p = desc_header.find_next_sibling("p")
        if desc_p:
            desc_text = desc_p.get_text(strip=True)
            if desc_text:
                description = desc_text

    # Return exactly the 8 required raw fields
    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": avail_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }
