import asyncio
import logging
from typing import Optional, Union, Dict, Any
from datetime import datetime

from .location_mapper import LocationMapper
from .weather_scraper import WeatherScraper
from .models import WeatherData, WeatherError, LocationMappingResult

logger = logging.getLogger(__name__)


class WeatherService:    
    def __init__(self, stations_file: Optional[str] = None):
        self.location_mapper = LocationMapper(stations_file)
        self.scraper = WeatherScraper()
        
    async def get_weather(self, location: str, 
                         include_forecast: bool = True,
                         similarity_threshold: float = 0.6) -> Union[WeatherData, WeatherError]:
        """Get weather data for a given location."""
        try:
            logger.info(f"Getting weather for location: {location}")
            
            # Map location to weather station
            mapping_result = self.location_mapper.map_location(location, similarity_threshold)
            
            if not mapping_result.success:
                return WeatherError(
                    error=mapping_result.error_message or "Location not found",
                    error_code="LOCATION_NOT_FOUND",
                    location=location,
                    timestamp=datetime.now()
                )
            
            # Scrape weather data
            async with self.scraper:
                weather_data = await self.scraper.scrape_weather(
                    mapping_result.url, 
                    mapping_result.mapped_location
                )
            
            # Remove forecast if not requested
            if not include_forecast:
                weather_data.forecast = None
            
            logger.info(f"Successfully retrieved weather for {mapping_result.mapped_location}")
            return weather_data
            
        except Exception as e:
            error_msg = f"Failed to get weather data: {str(e)}"
            logger.error(error_msg)
            
            return WeatherError(
                error=error_msg,
                error_code="SCRAPING_ERROR",
                location=location,
                timestamp=datetime.now()
            )
    
    def get_weather_sync(self, location: str, 
                        include_forecast: bool = True,
                        similarity_threshold: float = 0.6) -> Union[WeatherData, WeatherError]:
        """Synchronous wrapper for get_weather."""
        return asyncio.run(self.get_weather(location, include_forecast, similarity_threshold))
    
    async def get_weather_json(self, location: str,
                              include_forecast: bool = True,
                              similarity_threshold: float = 0.6) -> Dict[str, Any]:
        """Get weather data as JSON dictionary."""
        result = await self.get_weather(location, include_forecast, similarity_threshold)
        
        if isinstance(result, WeatherData):
            return result.dict()
        else:
            return result.dict()
    
    def get_weather_json_sync(self, location: str,
                             include_forecast: bool = True,
                             similarity_threshold: float = 0.6) -> Dict[str, Any]:
        """Synchronous wrapper for get_weather_json."""
        return asyncio.run(self.get_weather_json(location, include_forecast, similarity_threshold))
    
    def get_location_suggestions(self, location: str, 
                               limit: int = 5) -> LocationMappingResult:
        """Get location suggestions for a given location query."""
        mapping_result = self.location_mapper.map_location(location, threshold=0.3)
        
        # Limit suggestions
        if mapping_result.suggestions:
            mapping_result.suggestions = mapping_result.suggestions[:limit]
        
        return mapping_result
    
    def get_available_locations(self) -> list[str]:
        """Get list of all available weather station locations."""
        return self.location_mapper.get_all_locations()
    
    def validate_location(self, location: str) -> bool:
        """Check if a location is available."""
        mapping_result = self.location_mapper.map_location(location, threshold=0.8)
        return mapping_result.success
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check of the weather service."""
        health_status = {
            "service": "weather_service",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        try:
            # Check location mapper
            locations = self.location_mapper.get_all_locations()
            health_status["checks"]["location_mapper"] = {
                "status": "healthy" if locations else "unhealthy",
                "locations_count": len(locations)
            }
            
            # Test location mapping
            test_location = "Ho Chi Minh"
            mapping_result = self.location_mapper.map_location(test_location)
            health_status["checks"]["location_mapping"] = {
                "status": "healthy" if mapping_result.success else "degraded",
                "test_location": test_location,
                "mapped_successfully": mapping_result.success
            }
            
            # Test scraper (using a quick test)
            try:
                async with self.scraper:
                    # Just test if scraper can be initialized
                    health_status["checks"]["scraper"] = {
                        "status": "healthy",
                        "initialized": True
                    }
            except Exception as e:
                health_status["checks"]["scraper"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                health_status["status"] = "degraded"
            
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
        
        return health_status
    
    def health_check_sync(self) -> Dict[str, Any]:
        """Synchronous wrapper for health_check."""
        return asyncio.run(self.health_check())
