"""Pydantic models for weather data validation and serialization."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ForecastPeriod(BaseModel):
    """Individual forecast period data."""
    time: str = Field(..., description="Time period (e.g., '06:00', '12:00', '18:00')")
    temperature_c: Optional[int] = Field(None, description="Temperature in Celsius")
    condition: Optional[str] = Field(None, description="Weather condition description")
    humidity_percent: Optional[int] = Field(None, description="Humidity percentage")
    wind_speed_kmh: Optional[int] = Field(None, description="Wind speed in km/h")
    wind_direction: Optional[str] = Field(None, description="Wind direction")
    precipitation_chance: Optional[int] = Field(None, description="Precipitation chance percentage")


class WeatherForecast(BaseModel):
    """Weather forecast for specific days."""
    today: List[ForecastPeriod] = Field(default_factory=list, description="Today's forecast periods")
    tomorrow: List[ForecastPeriod] = Field(default_factory=list, description="Tomorrow's forecast periods")
    day_after: List[ForecastPeriod] = Field(default_factory=list, description="Day after tomorrow's forecast periods")


class CurrentWeather(BaseModel):
    """Current weather conditions."""
    temperature_c: Optional[int] = Field(None, description="Current temperature in Celsius")
    humidity_percent: Optional[int] = Field(None, description="Current humidity percentage")
    wind_speed_kmh: Optional[int] = Field(None, description="Current wind speed in km/h")
    wind_direction: Optional[str] = Field(None, description="Current wind direction")
    condition: Optional[str] = Field(None, description="Current weather condition")
    pressure_hpa: Optional[int] = Field(None, description="Atmospheric pressure in hPa")
    visibility_km: Optional[int] = Field(None, description="Visibility in kilometers")
    uv_index: Optional[int] = Field(None, description="UV index")


class WeatherData(BaseModel):
    """Complete weather data response model."""
    location: str = Field(..., description="Location name")
    source_url: str = Field(..., description="Source weather website URL")
    last_updated: datetime = Field(..., description="Last update timestamp")
    current: Optional[CurrentWeather] = Field(None, description="Current weather conditions")
    forecast: Optional[WeatherForecast] = Field(None, description="Weather forecast")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class WeatherError(BaseModel):
    """Weather service error response."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    location: Optional[str] = Field(None, description="Requested location")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    

class LocationSuggestion(BaseModel):
    """Location suggestion for invalid location requests."""
    suggested_location: str = Field(..., description="Suggested location name")
    similarity_score: float = Field(..., description="Similarity score (0-1)")
    url: str = Field(..., description="Weather URL for suggested location")


class LocationMappingResult(BaseModel):
    """Result of location mapping operation."""
    success: bool = Field(..., description="Whether mapping was successful")
    mapped_location: Optional[str] = Field(None, description="Mapped location name")
    url: Optional[str] = Field(None, description="Weather URL")
    suggestions: List[LocationSuggestion] = Field(default_factory=list, description="Alternative suggestions")
    error_message: Optional[str] = Field(None, description="Error message if mapping failed")
