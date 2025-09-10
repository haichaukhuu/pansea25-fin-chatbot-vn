import asyncio
import logging
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

from .models import ScrapedPage, CrawlResult
from .scraper import WebScraper, PlaywrightScraper
from .crawler import WebCrawler, SimpleCrawler

# Configure logging
logger = logging.getLogger(__name__)


class WebScrapingService:
    """
    Main web scraping service that provides high-level API for the chatbot.
    
    This service acts as the primary interface for all web scraping operations
    and can be easily integrated into the AgriFinHub backend.
    """
    
    def __init__(
        self,
        default_timeout: float = 30.0,
        default_max_pages: int = 20,
        enable_playwright: bool = True,
        default_same_domain: bool = True
    ):
        """
        Initialize the web scraping service.
        
        Args:
            default_timeout: Default timeout for requests
            default_max_pages: Default maximum pages to crawl
            enable_playwright: Enable Playwright fallback for JS-heavy sites
            default_same_domain: Default setting for same-domain crawling
        """
        self.default_timeout = default_timeout
        self.default_max_pages = default_max_pages
        self.enable_playwright = enable_playwright
        self.default_same_domain = default_same_domain
        
        # Initialize components
        self.scraper = WebScraper(timeout=default_timeout)
        self.playwright_scraper = PlaywrightScraper(timeout=default_timeout) if enable_playwright else None
        
        logger.info("WebScrapingService initialized")
    
    async def scrape_single_page(
        self, 
        url: str, 
        use_playwright: bool = False
    ) -> Dict[str, Any]:
        """
        Scrape a single web page and return structured JSON.
        
        Args:
            url: URL to scrape
            use_playwright: Force use of Playwright for JavaScript content
            
        Returns:
            Dictionary with scraped content in the specified JSON schema
        """
        try:
            logger.info(f"Scraping single page: {url}")
            
            # Choose scraper
            if use_playwright and self.playwright_scraper:
                page = await self.playwright_scraper.scrape_page(url)
            else:
                page = await self.scraper.scrape_page(url)
                
                # Fallback to Playwright if regular scraping failed
                if not page and self.playwright_scraper:
                    logger.info(f"Falling back to Playwright for: {url}")
                    page = await self.playwright_scraper.scrape_page(url)
            
            if page:
                result = {
                    "success": True,
                    "data": page.to_dict(),
                    "metadata": {
                        "scraping_method": "playwright" if use_playwright else "httpx",
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
                }
                logger.info(f"Successfully scraped: {url}")
                return result
            else:
                logger.error(f"Failed to scrape: {url}")
                return {
                    "success": False,
                    "error": "Failed to scrape page content",
                    "url": url,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
                
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def crawl_website(
        self,
        urls: Union[str, List[str]],
        depth: int = 1,
        max_pages: Optional[int] = None,
        same_domain_only: Optional[bool] = None,
        concurrent_requests: int = 3
    ) -> Dict[str, Any]:
        """
        Crawl a website starting from given URLs.
        
        Args:
            urls: Starting URL(s) - can be string or list of strings
            depth: Maximum crawl depth (0 = only start URLs, 1 = start + 1 level)
            max_pages: Maximum number of pages to crawl
            same_domain_only: Whether to only crawl same domain URLs
            concurrent_requests: Number of concurrent requests
            
        Returns:
            Dictionary with crawl results in the specified JSON schema
        """
        try:
            # Normalize URLs to list
            if isinstance(urls, str):
                url_list = [urls]
            else:
                url_list = urls
            
            # Apply defaults
            if max_pages is None:
                max_pages = self.default_max_pages
            if same_domain_only is None:
                same_domain_only = self.default_same_domain
            
            logger.info(f"Starting crawl of {len(url_list)} URLs with depth {depth}, "
                       f"max_pages {max_pages}, same_domain_only {same_domain_only}")
            
            # Initialize crawler
            crawler = WebCrawler(
                max_depth=depth,
                max_pages=max_pages,
                same_domain_only=same_domain_only,
                concurrent_requests=concurrent_requests,
                timeout=self.default_timeout,
                use_playwright_fallback=self.enable_playwright
            )
            
            # Perform crawl
            crawl_result = await crawler.crawl(url_list)
            
            # Format response
            result = {
                "success": True,
                "data": crawl_result.to_dict(),
                "metadata": {
                    "crawl_parameters": {
                        "start_urls": url_list,
                        "depth": depth,
                        "max_pages": max_pages,
                        "same_domain_only": same_domain_only,
                        "concurrent_requests": concurrent_requests
                    },
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
            
            logger.info(f"Crawl completed successfully. "
                       f"Pages: {crawl_result.successful_pages}, "
                       f"Errors: {crawl_result.failed_pages}")
            
            return result
            
        except Exception as e:
            logger.error(f"Crawl failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "urls": urls,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    async def simple_crawl(
        self,
        url: str,
        max_pages: int = 5
    ) -> Dict[str, Any]:
        """
        Simple crawl for basic use cases - lighter version of full crawling.
        
        Args:
            url: Starting URL
            max_pages: Maximum number of pages to crawl
            
        Returns:
            Dictionary with simplified crawl results
        """
        try:
            logger.info(f"Starting simple crawl of {url} with max_pages {max_pages}")
            
            crawler = SimpleCrawler(
                max_pages=max_pages,
                same_domain_only=True
            )
            
            crawl_result = await crawler.crawl_simple(url, depth=1)
            
            return {
                "success": True,
                "data": crawl_result.to_dict(),
                "metadata": {
                    "crawl_type": "simple",
                    "start_url": url,
                    "max_pages": max_pages,
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            }
            
        except Exception as e:
            logger.error(f"Simple crawl failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
    
    def format_for_ai(self, scrape_result: Dict[str, Any]) -> str:
        """
        Format scraping results for AI consumption.
        
        This method takes the structured JSON output and formats it into
        a more readable format that's optimized for AI processing.
        
        Args:
            scrape_result: Result from scrape_single_page or crawl_website
            
        Returns:
            Formatted string suitable for AI processing
        """
        try:
            if not scrape_result.get("success"):
                return f"Scraping failed: {scrape_result.get('error', 'Unknown error')}"
            
            data = scrape_result.get("data", {})
            
            if "pages" in data:
                # This is a crawl result
                pages = data["pages"]
                metadata = data.get("metadata", {})
                
                formatted = f"Web Crawl Results:\n"
                formatted += f"Total pages: {metadata.get('successful_pages', len(pages))}\n"
                formatted += f"Failed pages: {metadata.get('failed_pages', 0)}\n\n"
                
                for i, page in enumerate(pages, 1):
                    formatted += self._format_single_page(page, f"Page {i}")
                    formatted += "\n" + "="*50 + "\n\n"
                
            else:
                # This is a single page result
                formatted = self._format_single_page(data, "Scraped Page")
            
            return formatted
            
        except Exception as e:
            logger.error(f"Error formatting for AI: {str(e)}")
            return f"Error formatting results: {str(e)}"
    
    def _format_single_page(self, page: Dict[str, Any], title: str = "Page") -> str:
        """Format a single page for AI consumption"""
        formatted = f"{title}: {page.get('title', 'No Title')}\n"
        formatted += f"URL: {page.get('url', '')}\n"
        
        # Meta information
        meta = page.get('meta', {})
        if meta.get('description'):
            formatted += f"Description: {meta['description']}\n"
        
        # Headings
        headings = page.get('headings', {})
        for level, heading_list in headings.items():
            if heading_list:
                formatted += f"\n{level.upper()} Headings:\n"
                for heading in heading_list:
                    formatted += f"  - {heading}\n"
        
        # Content
        content = page.get('content', {})
        
        # Paragraphs
        paragraphs = content.get('paragraphs', [])
        if paragraphs:
            formatted += f"\nContent Paragraphs:\n"
            for i, para in enumerate(paragraphs[:5], 1):  # Limit to first 5 paragraphs
                formatted += f"{i}. {para[:200]}{'...' if len(para) > 200 else ''}\n"
        
        # Lists
        lists = content.get('lists', [])
        if lists:
            formatted += f"\nLists:\n"
            for i, list_items in enumerate(lists[:3], 1):  # Limit to first 3 lists
                formatted += f"List {i}:\n"
                for item in list_items[:5]:  # Limit items per list
                    formatted += f"  - {item}\n"
        
        # Tables
        tables = content.get('tables', [])
        if tables:
            formatted += f"\nTables: {len(tables)} table(s) found\n"
        
        # Links
        links = page.get('links', [])
        if links:
            formatted += f"\nLinks: {len(links)} link(s) found\n"
            # Show first few links
            for link in links[:5]:
                formatted += f"  - {link}\n"
        
        return formatted
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the scraping service.
        
        Returns:
            Dictionary with health status
        """
        try:
            # Test basic scraping with a simple page
            test_url = "https://httpbin.org/html"
            
            start_time = datetime.utcnow()
            result = await self.scrape_single_page(test_url)
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds()
            
            return {
                "status": "healthy" if result.get("success") else "degraded",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "response_time_seconds": response_time,
                "playwright_available": self.playwright_scraper is not None,
                "test_result": result.get("success", False)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": str(e),
                "playwright_available": self.playwright_scraper is not None
            }


# Global service instance (singleton pattern)
_service_instance: Optional[WebScrapingService] = None


def get_scraping_service() -> WebScrapingService:
    """
    Get the global web scraping service instance.
    
    Returns:
        WebScrapingService instance
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = WebScrapingService()
    return _service_instance


# Convenience functions for easy integration
async def scrape_url(url: str, use_playwright: bool = False) -> Dict[str, Any]:
    """
    Convenience function to scrape a single URL.
    
    Args:
        url: URL to scrape
        use_playwright: Force use of Playwright
        
    Returns:
        Scraping result dictionary
    """
    service = get_scraping_service()
    return await service.scrape_single_page(url, use_playwright)


async def crawl_urls(
    urls: Union[str, List[str]], 
    depth: int = 1, 
    max_pages: int = 10
) -> Dict[str, Any]:
    """
    Convenience function to crawl URLs.
    
    Args:
        urls: URL(s) to crawl
        depth: Crawl depth
        max_pages: Maximum pages to crawl
        
    Returns:
        Crawl result dictionary
    """
    service = get_scraping_service()
    return await service.crawl_website(urls, depth=depth, max_pages=max_pages)
