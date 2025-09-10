"""
Data models for web scraping and crawling service
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse


@dataclass
class ScrapedPage:
    """
    Represents a single scraped web page with structured content.
    
    This follows the JSON schema specified in the requirements:
    - URL and metadata
    - Structured content (headings, paragraphs, lists, tables)
    - Links and images
    - Crawl timestamp
    """
    url: str
    title: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)
    headings: Dict[str, List[str]] = field(default_factory=lambda: {
        "h1": [], "h2": [], "h3": [], "h4": [], "h5": [], "h6": []
    })
    content: Dict[str, Any] = field(default_factory=lambda: {
        "paragraphs": [],
        "lists": [],
        "tables": []
    })
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    crawled_on: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "url": self.url,
            "title": self.title,
            "meta": self.meta,
            "headings": self.headings,
            "content": self.content,
            "links": self.links,
            "images": self.images,
            "crawled_on": self.crawled_on
        }


@dataclass
class CrawlResult:
    """
    Represents the result of a web crawling operation.
    
    Contains multiple scraped pages and metadata about the crawl process.
    """
    pages: List[ScrapedPage] = field(default_factory=list)
    start_url: str = ""
    depth: int = 1
    total_pages: int = 0
    successful_pages: int = 0
    failed_pages: int = 0
    crawl_started: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    crawl_completed: str = ""
    errors: List[Dict[str, str]] = field(default_factory=list)
    
    def add_page(self, page: ScrapedPage) -> None:
        """Add a successfully scraped page"""
        self.pages.append(page)
        self.successful_pages += 1
        self.total_pages += 1
    
    def add_error(self, url: str, error: str) -> None:
        """Add a failed page with error details"""
        self.errors.append({
            "url": url,
            "error": error,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })
        self.failed_pages += 1
        self.total_pages += 1
    
    def complete_crawl(self) -> None:
        """Mark the crawl as completed"""
        self.crawl_completed = datetime.utcnow().isoformat() + "Z"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "pages": [page.to_dict() for page in self.pages],
            "metadata": {
                "start_url": self.start_url,
                "depth": self.depth,
                "total_pages": self.total_pages,
                "successful_pages": self.successful_pages,
                "failed_pages": self.failed_pages,
                "crawl_started": self.crawl_started,
                "crawl_completed": self.crawl_completed,
                "errors": self.errors
            }
        }


def normalize_url(url: str, base_url: str = "") -> str:
    """
    Normalize a URL by making it absolute and cleaning it up.
    
    Args:
        url: The URL to normalize
        base_url: The base URL to resolve relative URLs against
        
    Returns:
        Normalized absolute URL
    """
    if not url:
        return ""
    
    # Remove fragments and clean whitespace
    url = url.strip().split('#')[0]
    
    # Make absolute if relative
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    return url


def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs are from the same domain.
    
    Args:
        url1: First URL
        url2: Second URL
        
    Returns:
        True if same domain, False otherwise
    """
    try:
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2
    except Exception:
        return False


def is_valid_url(url: str) -> bool:
    """
    Check if a URL is valid and can be crawled.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.scheme in ('http', 'https')
    except Exception:
        return False
