# FlyRank Backend Track — Week 5 Assignment A9: The Polite Scraper

A production-minded, lightweight, and ethical web scraping pipeline written in Python. It collects book data across the first three catalogue pages of the Books to Scrape practice sandbox, normalizes messy text into clean data types, validates every record against strict Pydantic schemas, survives broken pages without crashing, and generates an honest operational report at the end of every run.

---

## 1. Target Classification

- **Target Website**: [Books to Scrape](https://books.toscrape.com/) (`https://books.toscrape.com/`)
- **Purpose**: Practice sandbox designed explicitly for developing and testing web scraping applications.
- **Scope**: Limited strictly to the first three catalogue pages (`page-1.html`, `page-2.html`, `page-3.html`), discovering exactly 60 unique books.
- **Data Collected**:
  - `title` (string)
  - `product_url` (canonical HTTPS URL)
  - `price_text` (raw currency string, e.g., `"£51.77"`)
  - `price_gbp` (numeric float, e.g., `51.77`)
  - `availability_text` (raw stock string, e.g., `"In stock (22 available)"`)
  - `rating_text` (star rating string, e.g., `"Three"`)
  - `description` (nullable string, `None` when absent)
  - `source_page` (provenance catalogue URL)
  - `fetched_at` (ISO 8601 UTC timestamp)
- **robots.txt Result**: `HTTP 404 (Not Found)`. Requesting `https://books.toscrape.com/robots.txt` returned no file. A missing `robots.txt` file is not treated as blanket permission to scrape without constraints.
- **Why This Target is Appropriate**: Books to Scrape explicitly states on its homepage: *"Warning! This is a demo website for web scraping purposes. Prices and ratings here were randomly assigned and have no real meaning."* It is intended solely for scraper education.
- **Core Principle**:
  > I will not reuse this code on another site without checking its rules and terms first.

---

## 2. Why No Browser Automation is Needed

The required book data is already present in the raw server-rendered HTML returned by the target website. Using browser automation tools like Selenium or Playwright would consume significantly more memory, CPU, and wall-clock execution time without adding value. Standard HTTP requests paired with an HTML parser provide a faster, more reliable, and lower-resource solution.

---

## 3. Architecture: Separation of Concerns

The scraper is structured as a clear, sequential data pipeline:

$$\text{Fetch} \longrightarrow \text{Extract} \longrightarrow \text{Normalize} \longrightarrow \text{Validate} \longrightarrow \text{Store} \longrightarrow \text{Report}$$

1. **Fetch (`src/fetcher.py`)**: Polite HTTP client with an identifying User-Agent, timeouts, rate-limiting delays, status code validation, resilient retry rules, and local disk caching.
2. **Extract (`src/parser.py`)**: Precise BeautifulSoup selectors targeting specific product information containers without global or ambiguous matches.
3. **Normalize (`src/normalizer.py`)**: Deterministic parsing of currency strings into floats and URL canonicalization to absolute HTTPS URLs.
4. **Validate (`src/models.py`)**: Strict Pydantic schema validation. Malformed or invalid records are isolated to `output/errors.json` and never enter `output/books.json`.
5. **Store (`src/main.py`)**: Idempotent storage indexed by canonical product URL. Re-running the pipeline always maintains 60 records and prevents duplication.
6. **Report (`src/reporter.py`)**: Real-time operational tracking that outputs timing, fetch counts, cache hits, validation numbers, and failure logs to `output/run-report.json`.

---

## 4. Politeness and Resilience Rules

- **Identifying User-Agent**: Every request sends an honest header naming the project and repository:
  `FlyRankInternship-A9/1.0 (+https://github.com/shubh6206/The-polite-scrapper)`
- **Request Timeout**: Every request is bounded by a 10-second timeout to prevent hanging connections.
- **Polite Rate Limiting**: Enforces a minimum **500 ms delay** between consecutive live network requests. Local cache reads bypass network delays.
- **Local Disk Caching**: Stores downloaded HTML under `cache/` during development. Subsequent runs read from disk (`[CACHE HIT]`), reducing server load.
- **Status Validation**: Only `HTTP 200` is treated as a successful fetch.
- **Resilience & Retry Policy**:
  - `HTTP 403 / 404`: Client refusals and missing resources are **never retried**.
  - `Timeouts / HTTP 5xx`: Server errors and timeouts are retried **exactly once** after a brief delay.
  - **Failure Isolation**: An individual detail page failure is logged and skipped without crashing the pipeline or discarding successfully parsed records.

---

## 5. Schema Definition

Validated records in `output/books.json` adhere to the following schema:

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `title` | `string` | Full title of the book | `"A Light in the Attic"` |
| `product_url` | `string` | Canonical absolute HTTPS product URL | `"https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"` |
| `price_text` | `string` | Raw scraped currency string | `"£51.77"` |
| `price_gbp` | `float` | Normalized numeric price in GBP | `51.77` |
| `availability_text` | `string` | Raw stock availability string | `"In stock (22 available)"` |
| `rating_text` | `string` | Star rating textual class | `"Three"` |
| `description` | `string \| null` | Product description (nullable if absent) | `"It's hard to imagine a world..."` |
| `source_page` | `string` | Provenance catalogue page where discovered | `"https://books.toscrape.com/catalogue/page-1.html"` |
| `fetched_at` | `string` | ISO 8601 UTC timestamp of retrieval | `"2026-08-23T12:00:00.000000+00:00"` |

---

## 6. Output Files

- `output/books.json`: Array of clean, schema-validated, deduplicated book records (exactly 60 items).
- `output/errors.json`: Array of rejected records that failed schema validation along with their error reason.
- `output/run-report.json`: Execution summary with timings, page counts, cache hits, and failure details.

### Example `output/run-report.json`
```json
{
  "start_time": "2026-08-23T07:56:00.000000+00:00",
  "duration_seconds": 1.45,
  "catalogue_pages": 3,
  "discovered_urls": 60,
  "unique_urls": 60,
  "pages_fetched": 63,
  "cache_hits": 0,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "failed_urls": []
}
```

---

## 7. Installation & Quick Start

### Prerequisites
- Python 3.10 or higher
- Git

### Setup in Under 2 Minutes

```bash
# 1. Clone the repository
git clone https://github.com/shubh6206/The-polite-scrapper.git
cd The-polite-scrapper/scraper

# 2. Create and activate a virtual environment
python3 -m venv .venv

# On Linux/macOS:
source .venv/bin/activate

# On Windows:
# .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Run the Scraper (Single Command)
```bash
python -m src.main
```

### Run the Unit Test Suite
```bash
pytest
# or using built-in unittest:
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## 8. Ethical Scraping Rules

1. **Use Official APIs**: Always prefer official APIs when available.
2. **Never Bypass Authentication**: Do not attempt to bypass logins, credentials, or session restrictions.
3. **Never Bypass Paywalls**: Respect content boundaries and commercial paywalls.
4. **Never Bypass Explicit Blocks**: Do not use CAPTCHA solvers, proxy rotation, or headers spoofing to circumvent bot protections.
5. **Collect Only What is Needed**: Restrict crawl depth and field collection to the minimum required scope.

---

## 9. Honest Limitations

- **Synchronous Execution**: The crawler executes synchronously to enforce politeness delays and prevent overloading the host server.
- **Fixed Scope**: Configured for the first 3 catalogue pages (60 books).
- **Static HTML**: Designed for server-rendered HTML; client-side single-page applications (SPAs) requiring dynamic DOM rendering would require a different architecture.
