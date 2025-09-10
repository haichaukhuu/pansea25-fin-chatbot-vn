
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Union, Dict, Any
import logging
from datetime import datetime

from external_services.web_scrap_crawl.service import (
    WebScrapingService,
    get_scraping_service
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/web-scraping", tags=["web-scraping"])


# Request/Response Models
class ScrapeUrlRequest(BaseModel):
    """Request model for single URL scraping."""
    url: HttpUrl
    use_playwright: bool = Field(default=False, description="Force use of Playwright for JavaScript content")
    
    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com",
                "use_playwright": False
            }
        }


class CrawlWebsiteRequest(BaseModel):
    """Request model for website crawling."""
    urls: Union[HttpUrl, List[HttpUrl]]
    depth: int = Field(default=1, ge=0, le=5, description="Maximum crawl depth (0-5)")
    max_pages: int = Field(default=20, ge=1, le=100, description="Maximum pages to crawl (1-100)")
    same_domain_only: bool = Field(default=True, description="Only crawl URLs from the same domain")
    concurrent_requests: int = Field(default=3, ge=1, le=10, description="Number of concurrent requests (1-10)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "urls": "https://example.com",
                "depth": 1,
                "max_pages": 10,
                "same_domain_only": True,
                "concurrent_requests": 3
            }
        }


class ScrapingResponse(BaseModel):
    """Standard response model for scraping operations."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: str
    response_time_seconds: Optional[float] = None
    playwright_available: bool
    test_result: Optional[bool] = None
    error: Optional[str] = None


# API Routes
@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check the health status of the web scraping service.
    
    Returns:
        HealthResponse: Service health information
    """
    try:
        service = get_scraping_service()
        health_data = await service.health_check()
        return HealthResponse(**health_data)
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.post("/scrape", response_model=ScrapingResponse)
async def scrape_single_page(request: ScrapeUrlRequest):
    """
    Scrape a single web page and return structured content.
    
    Args:
        request: ScrapeUrlRequest with URL and options
        
    Returns:
        ScrapingResponse: Scraped content in structured format
    """
    try:
        service = get_scraping_service()
        
        logger.info(f"Scraping single page: {request.url}")
        
        result = await service.scrape_single_page(
            url=str(request.url),
            use_playwright=request.use_playwright
        )
        
        return ScrapingResponse(
            success=result["success"],
            data=result.get("data"),
            error=result.get("error"),
            timestamp=result.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            metadata=result.get("metadata")
        )
        
    except Exception as e:
        logger.error(f"Scraping failed for {request.url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Scraping failed: {str(e)}"
        )


@router.post("/crawl", response_model=ScrapingResponse)
async def crawl_website(request: CrawlWebsiteRequest):
    """
    Crawl a website starting from given URLs.
    
    Args:
        request: CrawlWebsiteRequest with crawl configuration
        
    Returns:
        ScrapingResponse: Crawl results with multiple pages
    """
    try:
        service = get_scraping_service()
        
        # Convert URLs to list of strings
        if isinstance(request.urls, list):
            url_list = [str(url) for url in request.urls]
        else:
            url_list = [str(request.urls)]
        
        logger.info(f"Crawling {len(url_list)} URLs with depth {request.depth}")
        
        result = await service.crawl_website(
            urls=url_list,
            depth=request.depth,
            max_pages=request.max_pages,
            same_domain_only=request.same_domain_only,
            concurrent_requests=request.concurrent_requests
        )
        
        return ScrapingResponse(
            success=result["success"],
            data=result.get("data"),
            error=result.get("error"),
            timestamp=result.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            metadata=result.get("metadata")
        )
        
    except Exception as e:
        logger.error(f"Crawling failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Crawling failed: {str(e)}"
        )


@router.post("/simple-crawl")
async def simple_crawl(
    url: HttpUrl = Body(..., description="URL to crawl"),
    max_pages: int = Body(default=5, ge=1, le=20, description="Maximum pages to crawl")
):
    """
    Simple crawl for basic use cases.
    
    Args:
        url: Starting URL for crawling
        max_pages: Maximum number of pages to crawl
        
    Returns:
        Simplified crawl results
    """
    try:
        service = get_scraping_service()
        
        logger.info(f"Simple crawl of {url} with max_pages {max_pages}")
        
        result = await service.simple_crawl(
            url=str(url),
            max_pages=max_pages
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        logger.error(f"Simple crawl failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Simple crawl failed: {str(e)}"
        )


@router.post("/format-for-ai")
async def format_for_ai(scraping_result: Dict[str, Any] = Body(...)):
    """
    Format scraping results for AI consumption.
    
    Args:
        scraping_result: Result from scrape or crawl operation
        
    Returns:
        AI-formatted text representation
    """
    try:
        service = get_scraping_service()
        
        formatted_text = service.format_for_ai(scraping_result)
        
        return {
            "success": True,
            "formatted_text": formatted_text,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"AI formatting failed: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"AI formatting failed: {str(e)}"
        )


# Quick access endpoints with query parameters
@router.get("/quick-scrape")
async def quick_scrape(
    url: str = Query(..., description="URL to scrape"),
    playwright: bool = Query(default=False, description="Use Playwright for JavaScript content")
):
    """
    Quick scrape endpoint using query parameters.
    
    Args:
        url: URL to scrape
        playwright: Whether to use Playwright
        
    Returns:
        Scraped content
    """
    try:
        service = get_scraping_service()
        result = await service.scrape_single_page(url, use_playwright=playwright)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Quick scrape failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quick-crawl")
async def quick_crawl(
    url: str = Query(..., description="URL to crawl"),
    depth: int = Query(default=1, ge=0, le=3, description="Crawl depth"),
    max_pages: int = Query(default=10, ge=1, le=50, description="Maximum pages")
):
    """
    Quick crawl endpoint using query parameters.
    
    Args:
        url: Starting URL
        depth: Crawl depth
        max_pages: Maximum pages to crawl
        
    Returns:
        Crawl results
    """
    try:
        service = get_scraping_service()
        result = await service.crawl_website(
            urls=[url],
            depth=depth,
            max_pages=max_pages
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Quick crawl failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task endpoints for long-running operations
@router.post("/crawl-async")
async def crawl_async(
    background_tasks: BackgroundTasks,
    request: CrawlWebsiteRequest,
    callback_url: Optional[str] = Body(default=None)
):
    """
    Start an asynchronous crawl operation.
    
    Args:
        background_tasks: FastAPI background tasks
        request: Crawl configuration
        callback_url: Optional URL to POST results to when complete
        
    Returns:
        Task ID for tracking the operation
    """
    import uuid
    
    task_id = str(uuid.uuid4())
    
    def crawl_task(task_id: str, config: CrawlWebsiteRequest, callback: Optional[str]):
        """Background crawl task."""
        import asyncio
        
        async def run_crawl():
            try:
                service = get_scraping_service()
                
                # Convert URLs
                if isinstance(config.urls, list):
                    url_list = [str(url) for url in config.urls]
                else:
                    url_list = [str(config.urls)]
                
                result = await service.crawl_website(
                    urls=url_list,
                    depth=config.depth,
                    max_pages=config.max_pages,
                    same_domain_only=config.same_domain_only,
                    concurrent_requests=config.concurrent_requests
                )
                
                # Store result (in a real implementation, you'd use a database or cache)
                logger.info(f"Background crawl {task_id} completed: {result['success']}")
                
                # Send callback if provided
                if callback:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        try:
                            await client.post(callback, json={
                                "task_id": task_id,
                                "result": result
                            })
                        except Exception as e:
                            logger.error(f"Callback failed for task {task_id}: {str(e)}")
                
            except Exception as e:
                logger.error(f"Background crawl {task_id} failed: {str(e)}")
        
        # Run the async crawl
        asyncio.run(run_crawl())
    
    # Add to background tasks
    background_tasks.add_task(crawl_task, task_id, request, callback_url)
    
    return {
        "success": True,
        "task_id": task_id,
        "status": "started",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# WebSocket endpoint for real-time crawling updates
@router.websocket("/crawl-ws")
async def crawl_websocket(websocket):
    """
    WebSocket endpoint for real-time crawling updates.
    
    This would allow clients to receive live updates during crawling operations.
    """
    await websocket.accept()
    
    try:
        # In a real implementation, this would handle WebSocket crawling
        await websocket.send_text("WebSocket crawling not yet implemented")
        await websocket.close()
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close()

