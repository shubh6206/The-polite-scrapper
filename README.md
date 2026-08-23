# FlyRank Backend Track - Week 5 Assignment A9: The Polite Scraper

A lightweight, robust, and polite web scraping pipeline built in Python to collect structured book data from a public practice sandbox, normalize and validate records, handle errors gracefully, and generate transparent execution reports.

## Target Classification

- **Target Website**: [Books to Scrape](https://books.toscrape.com/) (`https://books.toscrape.com/`)
- **Purpose**: Practice sandbox designed explicitly for testing, learning, and developing web scraping applications.
- **Scope**: Limited strictly to the first three catalogue pages (`page-1.html`, `page-2.html`, `page-3.html`), discovering and extracting details for exactly 60 books.
- **Data Collected**:
  - `title` (string)
  - `product_url` (canonical HTTPS URL)
  - `price_text` (raw currency string, e.g., "£51.77")
  - `price_gbp` (numeric float, e.g., `51.77`)
  - `availability_text` (raw stock string, e.g., "In stock (22 available)")
  - `rating_text` (star rating string, e.g., "Three")
  - `description` (nullable string)
  - `source_page` (provenance catalogue URL)
  - `fetched_at` (ISO 8601 UTC timestamp)
- **robots.txt Result**: `HTTP 404 (Not Found)`. Requesting `https://books.toscrape.com/robots.txt` returned no file. A missing `robots.txt` file is not treated as blanket permission to scrape without constraints.
- **Why This Target is Appropriate**: Books to Scrape explicitly states on its pages: *"Warning! This is a demo website for web scraping purposes. Prices and ratings here were randomly assigned and have no real meaning."* It is intended solely for scraper education.
- **Ethical Rule**:
  > I will not reuse this code on another site without checking its rules and terms first.
