from typing import Dict, Any, Optional
from pydantic import Field
from langchain.tools import BaseTool
from external_services.weather_service.weather_service import WeatherService
from external_services.weather_service.models import WeatherData, WeatherError


class GetWeatherInfoTool(BaseTool):
    """Tool for retrieving weather information for agricultural planning."""
    
    name: str = "get_weather_info"
    description: str = "Useful for getting current weather and forecast information for a location in Vietnam to help with agricultural planning."
    return_direct: bool = False
    
    # Define fields for non-serializable attributes
    weather_service: Any = Field(default=None, exclude=True)
    
    # Pydantic v2 configuration
    model_config = {
        "arbitrary_types_allowed": True,
        "extra": "allow"
    }
    
    def __init__(self, **kwargs):
        """Initialize the weather information tool."""
        # Initialize parent class first
        super().__init__(**kwargs)
        
        # Set instance attributes after parent initialization
        self.weather_service = WeatherService()
    
    def _run(self, location: str, include_forecast: bool = True) -> Dict[str, Any]:
        """Run the tool to get weather information.
        
        Args:
            location: The location in Vietnam to get weather for
            include_forecast: Whether to include forecast data
            
        Returns:
            Dictionary with weather information
        """
        # Use the synchronous version of the weather service
        result = self.weather_service.get_weather_sync(
            location=location,
            include_forecast=include_forecast,
            similarity_threshold=0.5  # Lower threshold for better matching
        )
        
        # Convert to dictionary for easier handling
        if isinstance(result, WeatherData):
            return {
                "success": True,
                "location": result.location,
                "current_weather": {
                    "temperature": result.current_weather.temperature,
                    "humidity": result.current_weather.humidity,
                    "wind_speed": result.current_weather.wind_speed,
                    "wind_direction": result.current_weather.wind_direction,
                    "condition": result.current_weather.condition,
                    "timestamp": result.current_weather.timestamp.isoformat() if result.current_weather.timestamp else None
                },
                "forecast": [
                    {
                        "date": item.date.isoformat() if item.date else None,
                        "min_temp": item.min_temp,
                        "max_temp": item.max_temp,
                        "condition": item.condition
                    }
                    for item in (result.forecast or [])
                ] if include_forecast and result.forecast else None,
                "agricultural_impact": self._get_agricultural_impact(result)
            }
        else:  # WeatherError
            return {
                "success": False,
                "error": result.error,
                "error_code": result.error_code,
                "location": result.location,
                "timestamp": result.timestamp.isoformat() if result.timestamp else None,
                "suggestions": self._get_location_suggestions(location)
            }
    
    async def _arun(self, location: str, include_forecast: bool = True) -> Dict[str, Any]:
        """Async version of _run."""
        # For simplicity, we're just calling the sync version
        return self._run(location, include_forecast)
    
    def _get_location_suggestions(self, location: str) -> list[str]:
        """Get location suggestions if the provided location is not found."""
        mapping_result = self.weather_service.get_location_suggestions(location, limit=5)
        return [suggestion.name for suggestion in mapping_result.suggestions] if mapping_result.suggestions else []
    
    def _get_agricultural_impact(self, weather_data: WeatherData) -> Dict[str, str]:
        """Generate agricultural impact information based on weather data.
        
        This is a simple implementation that could be expanded with more
        sophisticated agricultural knowledge.
        """
        impacts = {}
        
        # Current weather impacts
        if weather_data.current_weather:
            temp = weather_data.current_weather.temperature
            humidity = weather_data.current_weather.humidity
            condition = weather_data.current_weather.condition.lower() if weather_data.current_weather.condition else ""
            
            # Temperature impacts
            if temp is not None:
                if temp > 35:
                    impacts["temperature"] = "High temperature may cause heat stress in crops. Consider additional irrigation."
                elif temp < 15:
                    impacts["temperature"] = "Low temperature may slow plant growth. Protect sensitive crops."
            
            # Humidity impacts
            if humidity is not None:
                if humidity > 80:
                    impacts["humidity"] = "High humidity increases risk of fungal diseases. Monitor crops closely."
                elif humidity < 40:
                    impacts["humidity"] = "Low humidity may increase water requirements. Adjust irrigation accordingly."
            
            # Condition impacts
            if "rain" in condition or "shower" in condition:
                impacts["condition"] = "Rainfall may reduce need for irrigation but increase disease risk."
            elif "storm" in condition or "thunder" in condition:
                impacts["condition"] = "Stormy conditions may damage crops. Consider protective measures."
            elif "sunny" in condition or "clear" in condition:
                impacts["condition"] = "Sunny conditions good for photosynthesis but may increase water requirements."
        
        return impacts