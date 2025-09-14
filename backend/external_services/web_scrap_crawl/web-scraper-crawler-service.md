# Web Crawling & Scraping Service

## Purpose

The **Web Crawling and Scraping Service** is an auxiliary backend module for **AgriFinHub’s AI chatbot**.  
Its goal is to **gather information from one or multiple web pages** and return it as a **structured JSON object** that the AI can process.

This service does **not** aim to be a full-fledged search engine crawler (like Googlebot).  
Instead, it provides:
- Targeted crawling from a starting URL (configurable depth).
- Structured extraction of page contents.
- JSON output suitable for AI ingestion.

Keep it modular – scraping and crawling are separate functions.

Expandable schema – can add images, tables, or other fields later.

AI-friendly JSON – structured into headings, paragraphs, and links.

Avoid raw HTML dumps – extract meaningful content only.
---

## File location
This feature and its files must be stored in: `backend\external_services\web_scrap_crawl`, and strictly follows the project structure in `directory.md`

---

## Workflow

The service is composed of two main parts: **Crawling** and **Scraping**.

### 1. Input
- **URL(s)**: Starting point(s) for crawling.  
- **Depth** *(optional)*: How many link levels deep to follow (default = 1).  

### 2. Fetching
- Fetch HTML content using `httpx` (async, fast) or `requests` (sync).  
- If the website is JavaScript-heavy, fallback to `playwright`.  

### 3. Parsing
From each HTML page, extract the following:
- **Title** (`<title>`)  
- **Meta description & keywords** (`<meta>`)  
- **Headings** (`<h1>, <h2>, …`)  
- **Paragraphs** (`<p>`)  
- **Lists & Tables** (optional structured content)  
- **Links** (`<a href>` → absolute URLs)  
- **Images** (`<img src>`)  

### 4. Crawling
- Collect all discovered links.  
- Apply filtering (e.g., same domain only).  
- Follow links until `depth` is reached.  

### 5. Structuring JSON
- Each page is stored as **one JSON object**.  
- Multiple crawled pages form a **list of JSON objects**.  

---

## JSON Output Schema

Example structure for **one page**:

```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "meta": {
    "description": "This domain is for illustrative examples in documents.",
    "keywords": ["example", "domain"],
    "other_meta": {
      "author": "IANA"
    }
  },
  "headings": {
    "h1": ["Example Domain"],
    "h2": [],
    "h3": []
  },
  "content": {
    "paragraphs": [
      "This domain is for use in illustrative examples in documents.",
      "You may use this domain in literature without prior coordination or asking for permission."
    ],
    "lists": [
      ["First item", "Second item"]
    ],
    "tables": [
      {
        "headers": ["Name", "Value"],
        "rows": [["Example", "123"]]
      }
    ]
  },
  "links": [
    "https://www.iana.org/domains/example"
  ],
  "images": [
    "https://example.com/image.png"
  ],
  "crawled_on": "2025-09-09T15:30:00Z"
}
