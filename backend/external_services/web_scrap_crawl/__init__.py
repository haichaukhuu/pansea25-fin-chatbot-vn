"""
Web Scraping and Crawling Service

A modular service for web scraping and crawling that provides:
- Structured HTML content extraction
- Configurable crawling depth
- JavaScript-heavy site support via Playwright fallback
- AI-friendly JSON output
"""

from .models import ScrapedPage, CrawlResult
from .scraper import WebScraper
from .crawler import WebCrawler
from .service import WebScrapingService, scrape_url, crawl_urls

__all__ = [
    'ScrapedPage',
    'CrawlResult', 
    'WebScraper',
    'WebCrawler',
    'WebScrapingService',
    'scrape_url',
    'crawl_urls'
]
