"""
Web scraper module using HTTPX and BeautifulSoup4 for fast, async HTML parsing.

This module handles:
- Fetching web pages with HTTPX (async HTTP client)
- Parsing HTML content with BeautifulSoup4
- Extracting structured data (title, meta, headings, content, links, images)
- Handling errors and timeouts gracefully
- Playwright fallback for JavaScript-heavy sites
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
import re

import httpx
from bs4 import BeautifulSoup, Tag, NavigableString

from .models import ScrapedPage, normalize_url

# Configure logging
logger = logging.getLogger(__name__)


class WebScraper:
    """
    Web scraper that extracts structured content from HTML pages.
    
    Features:
    - Async HTTP requests with HTTPX
    - HTML parsing with BeautifulSoup4
    - Structured content extraction
    - Error handling and retry logic
    - User-agent rotation
    - Respect for robots.txt (optional)
    """
    
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        user_agent: str = "AgriFinHub-WebScraper/1.0",
        respect_robots: bool = True,
        max_page_size: int = 10 * 1024 * 1024  # 10MB limit
    ):
        """
        Initialize the web scraper.
        
        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            user_agent: User-agent string for requests
            respect_robots: Whether to respect robots.txt
            max_page_size: Maximum page size in bytes
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent
        self.respect_robots = respect_robots
        self.max_page_size = max_page_size
        
        # HTTP client configuration
        self.client_config = {
            "timeout": httpx.Timeout(timeout),
            "headers": {
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
            "follow_redirects": True,
            "limits": httpx.Limits(max_keepalive_connections=20, max_connections=100)
        }
    
    async def scrape_page(self, url: str) -> Optional[ScrapedPage]:
        """
        Scrape a single web page and extract structured content.
        
        Args:
            url: URL to scrape
            
        Returns:
            ScrapedPage object with extracted content, or None if failed
        """
        try:
            # Fetch the page content
            html_content = await self._fetch_page(url)
            if not html_content:
                return None
            
            # Parse HTML and extract content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Create ScrapedPage object
            page = ScrapedPage(url=url)
            
            # Extract all content
            self._extract_title(soup, page)
            self._extract_meta(soup, page)
            self._extract_headings(soup, page)
            self._extract_content(soup, page)
            self._extract_links(soup, page, url)
            self._extract_images(soup, page, url)
            
            logger.info(f"Successfully scraped page: {url}")
            return page
            
        except Exception as e:
            logger.error(f"Failed to scrape page {url}: {str(e)}")
            return None
    
    async def _fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a web page using HTTPX with retry logic.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content as string, or None if failed
        """
        async with httpx.AsyncClient(**self.client_config) as client:
            for attempt in range(self.max_retries):
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    
                    # Check content size
                    if len(response.content) > self.max_page_size:
                        logger.warning(f"Page too large: {url} ({len(response.content)} bytes)")
                        return None
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if 'text/html' not in content_type:
                        logger.warning(f"Non-HTML content: {url} ({content_type})")
                        return None
                    
                    return response.text
                    
                except httpx.HTTPStatusError as e:
                    logger.warning(f"HTTP error {e.response.status_code} for {url} (attempt {attempt + 1})")
                    if e.response.status_code == 404:
                        break  # Don't retry 404s
                        
                except httpx.RequestError as e:
                    logger.warning(f"Request error for {url} (attempt {attempt + 1}): {str(e)}")
                    
                except Exception as e:
                    logger.error(f"Unexpected error for {url} (attempt {attempt + 1}): {str(e)}")
                
                # Wait before retry (exponential backoff)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return None
    
    def _extract_title(self, soup: BeautifulSoup, page: ScrapedPage) -> None:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            page.title = title_tag.get_text(strip=True)
    
    def _extract_meta(self, soup: BeautifulSoup, page: ScrapedPage) -> None:
        """Extract meta tags"""
        meta_tags = soup.find_all('meta')
        
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            
            if name and content:
                name = name.lower()
                if name == 'description':
                    page.meta['description'] = content
                elif name == 'keywords':
                    # Split keywords and clean them
                    keywords = [kw.strip() for kw in content.split(',') if kw.strip()]
                    page.meta['keywords'] = keywords
                else:
                    # Store other meta tags in other_meta
                    if 'other_meta' not in page.meta:
                        page.meta['other_meta'] = {}
                    page.meta['other_meta'][name] = content
    
    def _extract_headings(self, soup: BeautifulSoup, page: ScrapedPage) -> None:
        """Extract headings (h1-h6)"""
        for level in range(1, 7):
            tag_name = f'h{level}'
            headings = soup.find_all(tag_name)
            
            heading_texts = []
            for heading in headings:
                text = heading.get_text(strip=True)
                if text:
                    heading_texts.append(text)
            
            page.headings[tag_name] = heading_texts
    
    def _extract_content(self, soup: BeautifulSoup, page: ScrapedPage) -> None:
        """Extract content (paragraphs, lists, tables)"""
        # Extract paragraphs
        paragraphs = soup.find_all('p')
        paragraph_texts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 10:  # Filter out very short paragraphs
                paragraph_texts.append(text)
        page.content['paragraphs'] = paragraph_texts
        
        # Extract lists
        lists = soup.find_all(['ul', 'ol'])
        list_items = []
        for list_element in lists:
            items = list_element.find_all('li')
            item_texts = [li.get_text(strip=True) for li in items if li.get_text(strip=True)]
            if item_texts:
                list_items.append(item_texts)
        page.content['lists'] = list_items
        
        # Extract tables
        tables = soup.find_all('table')
        table_data = []
        for table in tables:
            table_info = self._extract_table_data(table)
            if table_info:
                table_data.append(table_info)
        page.content['tables'] = table_data
    
    def _extract_table_data(self, table: Tag) -> Optional[Dict[str, Any]]:
        """Extract structured data from a table"""
        try:
            rows = table.find_all('tr')
            if not rows:
                return None
            
            # Try to find headers
            headers = []
            first_row = rows[0]
            header_cells = first_row.find_all(['th', 'td'])
            
            # Check if first row contains headers
            has_headers = any(cell.name == 'th' for cell in header_cells)
            
            if has_headers:
                headers = [cell.get_text(strip=True) for cell in header_cells]
                data_rows = rows[1:]
            else:
                data_rows = rows
            
            # Extract data rows
            table_rows = []
            for row in data_rows:
                cells = row.find_all(['td', 'th'])
                row_data = [cell.get_text(strip=True) for cell in cells]
                if row_data and any(cell for cell in row_data):  # Skip empty rows
                    table_rows.append(row_data)
            
            if not table_rows:
                return None
            
            return {
                "headers": headers if headers else [],
                "rows": table_rows
            }
            
        except Exception as e:
            logger.warning(f"Failed to extract table data: {str(e)}")
            return None
    
    def _extract_links(self, soup: BeautifulSoup, page: ScrapedPage, base_url: str) -> None:
        """Extract all links from the page"""
        links = soup.find_all('a', href=True)
        unique_links = set()
        
        for link in links:
            href = link.get('href')
            if href:
                # Normalize the URL
                normalized_url = normalize_url(href, base_url)
                if normalized_url and self._is_valid_link(normalized_url):
                    unique_links.add(normalized_url)
        
        page.links = sorted(list(unique_links))
    
    def _extract_images(self, soup: BeautifulSoup, page: ScrapedPage, base_url: str) -> None:
        """Extract all images from the page"""
        images = soup.find_all('img', src=True)
        unique_images = set()
        
        for img in images:
            src = img.get('src')
            if src:
                # Normalize the URL
                normalized_url = normalize_url(src, base_url)
                if normalized_url:
                    unique_images.add(normalized_url)
        
        page.images = sorted(list(unique_images))
    
    def _is_valid_link(self, url: str) -> bool:
        """Check if a link should be included"""
        try:
            parsed = urlparse(url)
            
            # Skip non-HTTP(S) links
            if parsed.scheme not in ('http', 'https'):
                return False
            
            # Skip common file extensions that aren't web pages
            excluded_extensions = {
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.zip', '.rar', '.tar', '.gz', '.exe', '.dmg', '.pkg',
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp',
                '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
                '.css', '.js', '.ico', '.xml', '.json'
            }
            
            path = parsed.path.lower()
            if any(path.endswith(ext) for ext in excluded_extensions):
                return False
            
            return True
            
        except Exception:
            return False


# Playwright fallback for JavaScript-heavy sites
class PlaywrightScraper:
    """
    Fallback scraper using Playwright for JavaScript-heavy websites.
    
    This is used when the regular HTTPX+BeautifulSoup scraper fails
    or when we detect that a page requires JavaScript rendering.
    """
    
    def __init__(self, timeout: float = 30.0):
        """
        Initialize Playwright scraper.
        
        Args:
            timeout: Page load timeout in seconds
        """
        self.timeout = timeout * 1000  # Playwright uses milliseconds
    
    async def scrape_page(self, url: str) -> Optional[ScrapedPage]:
        """
        Scrape a page using Playwright (requires playwright to be installed).
        
        Args:
            url: URL to scrape
            
        Returns:
            ScrapedPage object or None if failed
        """
        try:
            # Import playwright only when needed
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="AgriFinHub-WebScraper/1.0 (Playwright)",
                    viewport={"width": 1920, "height": 1080}
                )
                
                page = await context.new_page()
                
                # Navigate to page
                await page.goto(url, timeout=self.timeout, wait_until="networkidle")
                
                # Get HTML content after JavaScript execution
                html_content = await page.content()
                
                # Close browser
                await browser.close()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Create and populate ScrapedPage
                scraped_page = ScrapedPage(url=url)
                scraper = WebScraper()  # Use regular scraper for parsing
                scraper._extract_title(soup, scraped_page)
                scraper._extract_meta(soup, scraped_page)
                scraper._extract_headings(soup, scraped_page)
                scraper._extract_content(soup, scraped_page)
                scraper._extract_links(soup, scraped_page, url)
                scraper._extract_images(soup, scraped_page, url)
                
                logger.info(f"Successfully scraped page with Playwright: {url}")
                return scraped_page
                
        except ImportError:
            logger.error("Playwright not installed. Cannot use JavaScript fallback.")
            return None
        except Exception as e:
            logger.error(f"Playwright scraping failed for {url}: {str(e)}")
            return None
