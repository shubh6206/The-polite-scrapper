"""
Parser Module - Extracts book links, pagination, and detail fields from HTML.
FlyRank Backend Track Week 5 Assignment A9
"""

from typing import List, Optional, Tuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup


def extract_catalogue_book_urls(html: str, base_url: str) -> List[str]:
    """
    Parses a catalogue page HTML and extracts all book product URLs.
    Converts relative links to absolute URLs using urllib.parse.urljoin.
    """
    soup = BeautifulSoup(html, "html.parser")
    book_urls: List[str] = []

    # Target specific product pod structures in the catalogue
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
