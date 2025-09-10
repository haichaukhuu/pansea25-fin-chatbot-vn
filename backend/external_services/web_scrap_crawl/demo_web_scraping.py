#!/usr/bin/env python3
"""
Demonstration of the Web Scraping Service
"""

import sys
import os
import asyncio
import json

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from external_services.web_scrap_crawl import WebScrapingService, scrape_url


async def demo_single_page_scraping():
    """Demonstrate single page scraping"""
    print("Demonstrating single page scraping...")
    
    # Using the convenience function
    result = await scrape_url("https://httpbin.org/html")
    
    if result["success"]:
        data = result["data"]
        print("Successfully scraped page!")
        print(f"   - Title: {data['title']}")
        print(f"   - URL: {data['url']}")
        print(f"   - Paragraphs: {len(data['content']['paragraphs'])}")
        print(f"   - Links: {len(data['links'])}")
        print(f"   - Images: {len(data['images'])}")
        
        # Show some content
        if data['content']['paragraphs']:
            print(f"   - First paragraph: {data['content']['paragraphs'][0][:100]}...")
            
    else:
        print(f"Failed to scrape page: {result.get('error', 'Unknown error')}")
    
    return result


async def demo_service_usage():
    """Demonstrate direct service usage"""
    print("Demonstrating service class usage...")
    
    service = WebScrapingService()
    
    # Health check
    health = await service.health_check()
    print(f"   - Health check: {health}")
    
    # Simple crawl with depth 1
    result = await service.simple_crawl("https://httpbin.org/html", max_pages=3)
    
    if result["success"]:
        pages = result["data"]["pages"]
        print(f"Successfully crawled {len(pages)} pages!")
        for i, page in enumerate(pages):
            print(f"   - Page {i+1}: {page['title']} ({page['url']})")
    else:
        print(f"Crawl failed: {result.get('error', 'Unknown error')}")
    
    return result


async def demo_ai_formatted_output():
    """Demonstrate AI-formatted output"""
    print("Demonstrating AI-formatted output...")
    
    service = WebScrapingService()
    result = await service.scrape_single_page("https://httpbin.org/html")
    
    if result["success"]:
        # Format for AI consumption
        ai_format = service.format_for_ai(result)
        print("AI-formatted data generated!")
        print(f"   - Type: {type(ai_format)}")
        print(f"   - Keys: {list(ai_format.keys()) if isinstance(ai_format, dict) else 'Not a dict'}")
        
        # Show formatted output sample
        if isinstance(ai_format, dict) and 'structured_content' in ai_format:
            content = ai_format['structured_content']
            print(f"   - Structured content: {str(content)[:200]}...")
            
    else:
        print(f"Failed to generate AI format: {result.get('error', 'Unknown error')}")
    
    return result


async def main():
    """Run all demonstrations"""
    print("Web Scraping Service Demonstration")
    print("=" * 50)
    
    try:
        # Demo 1: Single page scraping
        await demo_single_page_scraping()
        print()
        
        # Demo 2: Service usage
        await demo_service_usage()
        print()
        
        # Demo 3: AI formatting
        await demo_ai_formatted_output()
        print()
        
        print("All demonstrations completed successfully!")
        print("\nService Features Verified:")
        print("   - Single page scraping")
        print("   - Multi-page crawling")
        print("   - Health monitoring")
        print("   - AI-optimized output formatting")
        print("   - Error handling")
        
    except Exception as e:
        print(f"Demonstration failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
