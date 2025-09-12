from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
import logging

from external_services.weather_service import WeatherService, WeatherData, WeatherError

logger = logging.getLogger(__name__)

# Create router
weather_router = APIRouter(prefix="/weather", tags=["weather"])

# Initialize weather service lazily
weather_service = None

def get_weather_service() -> WeatherService:
    """Dependency to get weather service instance."""
    global weather_service
    if weather_service is None:
        try:
            weather_service = WeatherService()
            logger.info("Weather service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize weather service: {str(e)}")
            raise HTTPException(status_code=503, detail="Weather service not available")
    return weather_service


# Request/Response models
class WeatherRequest(BaseModel):
    """Weather request model."""
    location: str = Field(..., description="Location name or query", min_length=1, max_length=100)
    include_forecast: bool = Field(default=True, description="Include weather forecast")
    similarity_threshold: float = Field(default=0.6, description="Location matching threshold", ge=0.0, le=1.0)


class WeatherResponse(BaseModel):
    """Weather response model."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Union[WeatherData, WeatherError]] = Field(None, description="Weather data or error information")
    message: Optional[str] = Field(None, description="Additional message")


class LocationSuggestionsResponse(BaseModel):
    """Location suggestions response model."""
    success: bool = Field(..., description="Whether suggestions were found")
    suggestions: List[Dict[str, Any]] = Field(default_factory=list, description="List of location suggestions")
    message: Optional[str] = Field(None, description="Additional message")


class HealthCheckResponse(BaseModel):
    """Health check response model."""
    service: str = Field(..., description="Service name")
    status: str = Field(..., description="Health status")
    timestamp: str = Field(..., description="Check timestamp")
    checks: Dict[str, Any] = Field(..., description="Individual component checks")


@weather_router.get("/", response_model=WeatherResponse)
async def get_weather(
    location: str = Query(..., description="Location name or query", min_length=1, max_length=100),
    include_forecast: bool = Query(default=True, description="Include weather forecast"),
    similarity_threshold: float = Query(default=0.6, description="Location matching threshold", ge=0.0, le=1.0),
    service: WeatherService = Depends(get_weather_service)
) -> WeatherResponse:
    """Get weather data for a specified location.
    """
    try:
        logger.info(f"Weather request for location: {location}")
        
        result = await service.get_weather(
            location=location,
            include_forecast=include_forecast,
            similarity_threshold=similarity_threshold
        )
        
        if isinstance(result, WeatherData):
            return WeatherResponse(
                success=True,
                data=result,
                message=f"Weather data retrieved successfully for {result.location}"
            )
        else:
            # WeatherError case
            return WeatherResponse(
                success=False,
                data=result,
                message=result.error
            )
            
    except Exception as e:
        logger.error(f"Error processing weather request for {location}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Failed to process weather request",
                "location": location
            }
        )


@weather_router.post("/", response_model=WeatherResponse)
async def get_weather_post(
    request: WeatherRequest,
    service: WeatherService = Depends(get_weather_service)
) -> WeatherResponse:
    """Get weather data for a specified location (POST method).
    """
    try:
        logger.info(f"Weather POST request for location: {request.location}")
        
        result = await service.get_weather(
            location=request.location,
            include_forecast=request.include_forecast,
            similarity_threshold=request.similarity_threshold
        )
        
        if isinstance(result, WeatherData):
            return WeatherResponse(
                success=True,
                data=result,
                message=f"Weather data retrieved successfully for {result.location}"
            )
        else:
            # WeatherError case
            return WeatherResponse(
                success=False,
                data=result,
                message=result.error
            )
            
    except Exception as e:
        logger.error(f"Error processing weather POST request for {request.location}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error", 
                "message": "Failed to process weather request",
                "location": request.location
            }
        )


@weather_router.get("/suggestions", response_model=LocationSuggestionsResponse)
async def get_location_suggestions(
    location: str = Query(..., description="Location query for suggestions", min_length=1, max_length=100),
    limit: int = Query(default=5, description="Maximum number of suggestions", ge=1, le=20),
    service: WeatherService = Depends(get_weather_service)
) -> LocationSuggestionsResponse:
    """Get location suggestions for a location query.
    """
    try:
        logger.info(f"Getting location suggestions for: {location}")
        
        mapping_result = service.get_location_suggestions(location, limit)
        
        suggestions = []
        if mapping_result.success and mapping_result.mapped_location:
            # Add the best match first
            suggestions.append({
                "location": mapping_result.mapped_location,
                "url": mapping_result.url,
                "similarity_score": 1.0,
                "type": "best_match"
            })
        
        # Add other suggestions
        for suggestion in mapping_result.suggestions:
            suggestions.append({
                "location": suggestion.suggested_location,
                "url": suggestion.url,
                "similarity_score": suggestion.similarity_score,
                "type": "suggestion"
            })
        
        return LocationSuggestionsResponse(
            success=len(suggestions) > 0,
            suggestions=suggestions,
            message=f"Found {len(suggestions)} suggestions for '{location}'" if suggestions 
                   else f"No suggestions found for '{location}'"
        )
        
    except Exception as e:
        logger.error(f"Error getting location suggestions for {location}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Failed to get location suggestions",
                "location": location
            }
        )


@weather_router.get("/locations")
async def get_available_locations(
    service: WeatherService = Depends(get_weather_service)
) -> Dict[str, Any]:
    """Get list of all available weather station locations.
    """
    try:
        locations = service.get_available_locations()
        
        return {
            "success": True,
            "locations": locations,
            "count": len(locations),
            "message": f"Retrieved {len(locations)} available weather stations"
        }
        
    except Exception as e:
        logger.error(f"Error getting available locations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Failed to get available locations"
            }
        )


@weather_router.get("/validate/{location}")
async def validate_location(
    location: str,
    service: WeatherService = Depends(get_weather_service)
) -> Dict[str, Any]:
    """Validate if a location is available for weather data.
    """
    try:
        is_valid = service.validate_location(location)
        
        return {
            "success": True,
            "location": location,
            "is_valid": is_valid,
            "message": f"Location '{location}' is {'valid' if is_valid else 'invalid'}"
        }
        
    except Exception as e:
        logger.error(f"Error validating location {location}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Failed to validate location",
                "location": location
            }
        )


@weather_router.get("/health", response_model=HealthCheckResponse)
async def health_check(
    service: WeatherService = Depends(get_weather_service)
) -> HealthCheckResponse:
    """Perform health check of the weather service.
    """
    try:
        health_status = await service.health_check()
        return HealthCheckResponse(**health_status)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "Service unhealthy",
                "message": "Weather service health check failed"
            }
        )
