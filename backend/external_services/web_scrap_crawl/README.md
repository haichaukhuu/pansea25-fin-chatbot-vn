# Web Scraping & Crawling Service (Concise Guide)

High‑level async service for extracting structured, AI‑ready text + metadata from individual pages or whole sites. Used by the AgriFinHub backend to enrich chat context with trustworthy external content.

---
## 1. Core Idea
You give URLs → the service (a) fetches & parses HTML (optionally renders JS) → normalizes content → returns a compact JSON schema (pages + metadata) ready for embedding / LLM consumption.

---
## 2. Architecture & Workflow
```
Caller ─► WebScrapingService ─┬─► WebScraper (httpx + BeautifulSoup) ─► Parse / Extract
                              │
                              └─► (Optional) PlaywrightScraper ─► Render JS then parse
                              │
                              └─► WebCrawler (queue, depth, politeness) ─► uses WebScraper/Playwright per page
```
Flow (single page): input URL → choose plain fetch or JS render → extract (title, meta, headings, text blocks, lists, tables, links, images) → return `ScrapedPage`.

Flow (crawl): seed URLs → queue (BFS up to depth & max_pages) → filter links (domain / dedupe / size) → per page scrape → accumulate pages + errors → return `CrawlResult`.

Error handling: retries (transient), graceful skip on parse/HTTP errors, structured error list.

---
## 3. When to Use What
| Need                                            | Use                                      |
|-------------------------------------------------|------------------------------------------|
| One page only                                   | `scrape_single_page` / `scrape_url` |
| Small site / section                            | `simple_crawl` |
| Controlled multi‑URL crawl (depth, concurrency) | `crawl_website` / `crawl_urls` |
| JS heavy (SPAs, dynamic tables)                 | pass `use_playwright=True` or enable fallback |

---
## 4. Primary Python APIs
Import path inside backend:
```python
from external_services.web_scrap_crawl import (
    WebScrapingService, scrape_url, crawl_urls
)
```
Service methods:
```python
await service.scrape_single_page(url, use_playwright=False)
await service.crawl_website(urls, depth=1, max_pages=20, same_domain_only=True,
                             concurrent_requests=3)
await service.simple_crawl(url, max_pages=5)              # convenience single root
service.format_for_ai(result_or_page)                     # flatten pages for LLM
await service.health_check()
```
Top‑level convenience (bypass manual service creation):
```python
await scrape_url(url, use_playwright=False)
await crawl_urls(urls, depth=1, max_pages=10)
```

Minimal example:
```python
service = WebScrapingService(enable_playwright=False)
single = await service.scrape_single_page("https://example.com")
if single["success"]:
    print(single["data"]["title"])

crawl = await service.crawl_website(["https://example.com"], depth=1, max_pages=8)
print(len(crawl["data"]["pages"]))
```

---
## 5. Returned Data (Simplified Schemas)
ScrapedPage:
```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "meta": {"description": "...", "keywords": [], "other_meta": {}},
  "headings": {"h1": ["..."], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []},
  "content": {
    "paragraphs": ["text block", "..."],
    "lists": [["li1", "li2"]],
    "tables": [{"headers": ["Col1"], "rows": [["Val1"]]}]
  },
  "links": ["https://example.com/next"],
  "images": ["https://example.com/logo.png"],
  "crawled_on": "ISO8601"
}
```
Generic success envelope:
```json
{"success": true, "data": { /* ScrapedPage OR CrawlResult.data */ }, "metadata": {...}}
```
CrawlResult (`data` portion):
```json
{
  "pages": [/* ScrapedPage objects */],
  "metadata": {
    "start_url": "https://example.com",
    "depth": 1,
    "total_pages": 8,
    "successful_pages": 8,
    "failed_pages": 0,
    "errors": []
  }
}
```
Error example:
```json
{"success": false, "error": "Timeout", "url": "https://...", "timestamp": "ISO"}
```

For LLM ingestion you can call:
```python
ai_pages = service.format_for_ai(crawl)
```
which returns a flattened list of {source_url, title, text, crawled_on} objects.

---
## 6. Tunable Parameters
You adjust these at construction or per call.

WebScrapingService:
- `default_timeout` (float, seconds) – baseline network timeout.
- `default_max_pages` – fallback limit when not specified.
- `enable_playwright` (bool) – allow JS rendering path.
- `default_same_domain` (bool) – restrict cross‑domain expansion.

Scrape call flags:
- `use_playwright` – force JS rendering for that page.

Crawl method parameters:
- `urls` (List[str]) – seeds.
- `depth` (int) – BFS link depth (0 = seeds only).
- `max_pages` (int) – hard cap; stops once reached.
- `same_domain_only` (bool) – keep links under original host(s).
- `concurrent_requests` (int) – parallel fetch workers (respectful: 3‑5 typical).
- `delay_between_requests` (float) – politeness delay between fetches.
- `use_playwright_fallback` (bool) – only render if plain fetch fails.
- `timeout` (float) – per request override.

WebScraper internal options (constructor):
- `max_retries` – transient retry attempts.
- `user_agent` – custom UA string.
- `respect_robots` – skip pages disallowed by robots.txt.
- `max_page_size` – bytes limit (drop oversized pages).

---
## 7. Choosing Playwright
Use Playwright when: content appears only after JS, critical data in dynamic tables, or anti‑bot needs full browser. Skip it for static news, docs, government HTML, to save latency & infra.

---
## 8. REST Endpoints (FastAPI Layer)
Base path: `/api/v1/web-scraping/`
- `GET /health`
- `POST /scrape`  body: `{ "url": str, "use_playwright": bool? }`
- `POST /crawl`   body: `{ "urls": List[str]|str, depth?, max_pages?, same_domain_only?, concurrent_requests? }`
- `GET /quick-scrape?url=...&playwright=false`
- `GET /quick-crawl?urls=...&depth=1&max_pages=5`

All return the success envelope described above.

---
## 9. Integration Pattern (Example Inside Chat Flow)
```python
async def enrich_context(user_query: str, urls: list[str]):
    service = WebScrapingService(enable_playwright=False)
    pages = []
    for u in urls:
        r = await service.scrape_single_page(u)
        if r["success"]:
            pages.append(service.format_for_ai(r))
    return {"user_query": user_query, "sources": pages}
```

---
## 10. Error Handling & Retries
- Transient network errors: retry with backoff (up to `max_retries`).
- Hard HTTP errors (404/403/500): recorded in `errors` list; crawl continues.
- Oversize / disallowed / parse failures: skipped & logged.
You always get either `{"success": true, ...}` or `{"success": false, "error": "..."}`.

---
## 11. Performance & Respectful Crawling
- Keep `concurrent_requests` moderate (≤5) unless whitelisted.
- Limit `depth` & `max_pages` to reduce noise and cost.
- Prefer static scrape first; enable JS only where needed.
- Use `same_domain_only=True` to avoid drift & reduce risk.

Quick tuning example:
```python
service = WebScrapingService(default_timeout=15.0, enable_playwright=False)
result = await service.crawl_website(["https://fast-site.com"], depth=1,
                                     max_pages=12, concurrent_requests=5)
```

---
## 12. Testing & Demo
Run tests:
```
python backend/external_services/web_scrap_crawl/test_web_scraping.py
```
Run interactive demo:
```
python backend/external_services/web_scrap_crawl/demo_web_scraping.py
```

---
## 13. Extending
Add new extraction logic by enhancing the scraper or post‑processing in `format_for_ai`. Keep JSON additions backward compatible.

---
## 14. Quick Reference
| Action                        | Call |
|-------------------------------|-------------------------------------------------------------|
| Single page (fast)            | `await scrape_url(url)` |
| Single page (needs JS)        | `await scrape_url(url, use_playwright=True)` |
| Seed crawl (light)            | `await service.simple_crawl(url, max_pages=5)` |
| Controlled multi‑seed crawl   | `await service.crawl_website(urls, depth=2, max_pages=40)` |
| Flatten for LLM               | `service.format_for_ai(crawl_result)` |
| Health check                  | `await service.health_check()` |

