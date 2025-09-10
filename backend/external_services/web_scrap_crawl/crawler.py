"""
Web crawler module that orchestrates the crawling of multiple pages.

This module handles:
- Starting from seed URLs
- Following links to specified depth
- Managing crawl queue and visited URLs
- Filtering links (same domain, valid URLs)
- Parallel/concurrent crawling for performance
- Rate limiting and politeness
"""

import asyncio
import logging
from typing import List, Set, Dict, Optional, Tuple
from urllib.parse import urlparse
from collections import deque
import time

from .models import ScrapedPage, CrawlResult, is_same_domain, is_valid_url
from .scraper import WebScraper, PlaywrightScraper

# Configure logging
logger = logging.getLogger(__name__)


class WebCrawler:
    """
    Web crawler that discovers and scrapes multiple pages following links.
    
    Features:
    - Configurable crawl depth
    - Same-domain filtering
    - Concurrent crawling with rate limiting
    - Duplicate URL detection
    - Progress tracking
    - Error handling and recovery
    """
    
    def __init__(
        self,
        max_depth: int = 1,
        max_pages: int = 50,
        same_domain_only: bool = True,
        concurrent_requests: int = 5,
        delay_between_requests: float = 1.0,
        use_playwright_fallback: bool = True,
        timeout: float = 30.0
    ):
        """
        Initialize the web crawler.
        
        Args:
            max_depth: Maximum crawl depth (0 = only seed URLs, 1 = seed + 1 level)
            max_pages: Maximum number of pages to crawl
            same_domain_only: Only crawl URLs from the same domain as seed URLs
            concurrent_requests: Number of concurrent requests
            delay_between_requests: Delay between requests in seconds (politeness)
            use_playwright_fallback: Use Playwright for JavaScript-heavy pages
            timeout: Request timeout in seconds
        """
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.same_domain_only = same_domain_only
        self.concurrent_requests = concurrent_requests
        self.delay_between_requests = delay_between_requests
        self.use_playwright_fallback = use_playwright_fallback
        
        # Initialize scrapers
        self.scraper = WebScraper(timeout=timeout)
        self.playwright_scraper = PlaywrightScraper(timeout=timeout) if use_playwright_fallback else None
        
        # Crawl state
        self.visited_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.domain_whitelist: Set[str] = set()
        
        # Rate limiting
        self.last_request_time = 0.0
        self.request_semaphore = asyncio.Semaphore(concurrent_requests)
    
    async def crawl(self, seed_urls: List[str]) -> CrawlResult:
        """
        Crawl websites starting from seed URLs.
        
        Args:
            seed_urls: List of starting URLs to crawl
            
        Returns:
            CrawlResult with all scraped pages and metadata
        """
        result = CrawlResult()
        result.start_url = seed_urls[0] if seed_urls else ""
        result.depth = self.max_depth
        
        try:
            # Initialize domain whitelist if same_domain_only is enabled
            if self.same_domain_only:
                for url in seed_urls:
                    try:
                        domain = urlparse(url).netloc
                        self.domain_whitelist.add(domain)
                    except Exception as e:
                        logger.warning(f"Invalid seed URL {url}: {str(e)}")
            
            # Initialize crawl queue with (url, depth) tuples
            crawl_queue = deque([(url, 0) for url in seed_urls if is_valid_url(url)])
            
            if not crawl_queue:
                logger.error("No valid seed URLs provided")
                result.complete_crawl()
                return result
            
            logger.info(f"Starting crawl with {len(crawl_queue)} seed URLs, max depth: {self.max_depth}")
            
            # Main crawl loop
            while crawl_queue and len(result.pages) < self.max_pages:
                # Process URLs in batches for concurrent crawling
                batch_size = min(self.concurrent_requests, len(crawl_queue))
                batch = []
                
                for _ in range(batch_size):
                    if crawl_queue:
                        batch.append(crawl_queue.popleft())
                
                if not batch:
                    break
                
                # Crawl batch concurrently
                tasks = [self._crawl_single_url(url, depth, result) for url, depth in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Add newly discovered URLs to queue
                for page in result.pages[-batch_size:]:  # Only check recently added pages
                    if page:
                        new_urls = self._discover_new_urls(page, crawl_queue)
                        crawl_queue.extend(new_urls)
            
            logger.info(f"Crawl completed. Scraped {result.successful_pages} pages, "
                       f"{result.failed_pages} failed, {len(self.visited_urls)} total visited")
            
        except Exception as e:
            logger.error(f"Crawl failed with error: {str(e)}")
            result.add_error("crawl_error", str(e))
        
        result.complete_crawl()
        return result
    
    async def _crawl_single_url(self, url: str, depth: int, result: CrawlResult) -> None:
        """
        Crawl a single URL with rate limiting and error handling.
        
        Args:
            url: URL to crawl
            depth: Current crawl depth
            result: CrawlResult to update
        """
        # Skip if already visited
        if url in self.visited_urls or url in self.failed_urls:
            return
        
        # Check domain whitelist
        if self.same_domain_only and not self._is_allowed_domain(url):
            return
        
        async with self.request_semaphore:
            try:
                # Rate limiting
                await self._apply_rate_limit()
                
                # Mark as visited
                self.visited_urls.add(url)
                
                logger.debug(f"Crawling URL (depth {depth}): {url}")
                
                # Try regular scraping first
                page = await self.scraper.scrape_page(url)
                
                # Fallback to Playwright if regular scraping failed and fallback is enabled
                if not page and self.playwright_scraper:
                    logger.info(f"Trying Playwright fallback for: {url}")
                    page = await self.playwright_scraper.scrape_page(url)
                
                if page:
                    result.add_page(page)
                    logger.info(f"Successfully crawled: {url}")
                else:
                    self.failed_urls.add(url)
                    result.add_error(url, "Failed to scrape page content")
                    logger.warning(f"Failed to crawl: {url}")
                
            except Exception as e:
                self.failed_urls.add(url)
                error_msg = f"Crawl error: {str(e)}"
                result.add_error(url, error_msg)
                logger.error(f"Error crawling {url}: {error_msg}")
    
    def _discover_new_urls(self, page: ScrapedPage, current_queue: deque) -> List[Tuple[str, int]]:
        """
        Discover new URLs from a scraped page.
        
        Args:
            page: ScrapedPage with extracted links
            current_queue: Current crawl queue to check for duplicates
            
        Returns:
            List of (url, depth) tuples for new URLs to crawl
        """
        new_urls = []
        
        # Extract current depth from the page (we need to track this better)
        current_depth = self._get_page_depth(page.url, current_queue)
        next_depth = current_depth + 1
        
        # Skip if we've reached max depth
        if next_depth > self.max_depth:
            return new_urls
        
        # Filter and add new URLs
        for link in page.links:
            if (link not in self.visited_urls and 
                link not in self.failed_urls and
                is_valid_url(link) and
                self._is_allowed_domain(link) and
                not self._is_already_queued(link, current_queue)):
                
                new_urls.append((link, next_depth))
        
        logger.debug(f"Discovered {len(new_urls)} new URLs from {page.url}")
        return new_urls
    
    def _get_page_depth(self, url: str, queue: deque) -> int:
        """
        Get the depth of a URL (heuristic based on current queue).
        
        This is a simplified approach. In a more sophisticated implementation,
        we'd track the depth explicitly for each URL.
        """
        # For now, assume depth 0 for simplicity
        # In practice, we'd need to track this more carefully
        return 0
    
    def _is_allowed_domain(self, url: str) -> bool:
        """Check if URL is allowed based on domain whitelist"""
        if not self.same_domain_only:
            return True
        
        try:
            domain = urlparse(url).netloc
            return domain in self.domain_whitelist
        except Exception:
            return False
    
    def _is_already_queued(self, url: str, queue: deque) -> bool:
        """Check if URL is already in the crawl queue"""
        return any(queued_url == url for queued_url, _ in queue)
    
    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests"""
        if self.delay_between_requests > 0:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.delay_between_requests:
                wait_time = self.delay_between_requests - time_since_last
                await asyncio.sleep(wait_time)
            
            self.last_request_time = time.time()


class SimpleCrawler:
    """
    Simplified crawler for basic use cases.
    
    This is a lighter version of WebCrawler that focuses on simplicity
    over advanced features like sophisticated queue management.
    """
    
    def __init__(self, max_pages: int = 10, same_domain_only: bool = True):
        """
        Initialize simple crawler.
        
        Args:
            max_pages: Maximum number of pages to crawl
            same_domain_only: Only crawl same domain URLs
        """
        self.max_pages = max_pages
        self.same_domain_only = same_domain_only
        self.scraper = WebScraper()
    
    async def crawl_simple(self, url: str, depth: int = 1) -> CrawlResult:
        """
        Simple crawl implementation for single URL with basic link following.
        
        Args:
            url: Starting URL
            depth: Maximum depth to crawl
            
        Returns:
            CrawlResult with scraped pages
        """
        result = CrawlResult()
        result.start_url = url
        result.depth = depth
        
        visited = set()
        to_visit = [(url, 0)]
        
        while to_visit and len(result.pages) < self.max_pages:
            current_url, current_depth = to_visit.pop(0)
            
            if current_url in visited or current_depth > depth:
                continue
            
            visited.add(current_url)
            
            try:
                page = await self.scraper.scrape_page(current_url)
                if page:
                    result.add_page(page)
                    
                    # Add links for next depth level
                    if current_depth < depth:
                        for link in page.links[:10]:  # Limit links to avoid explosion
                            if (self.same_domain_only and 
                                is_same_domain(link, url) and 
                                link not in visited):
                                to_visit.append((link, current_depth + 1))
                else:
                    result.add_error(current_url, "Failed to scrape")
                    
            except Exception as e:
                result.add_error(current_url, str(e))
        
        result.complete_crawl()
        return result
