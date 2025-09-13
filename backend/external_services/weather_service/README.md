# Weather Service External Tool

## Overview

The Weather Service is a comprehensive external tool designed for the AI Chatbot to provide real-time weather information for locations in Vietnam. It integrates with Vietnamese weather websites to deliver accurate, localized weather data.

## Features

- **Location Mapping**: Intelligent mapping of user queries to 63 Vietnamese weather stations
- **Fuzzy Matching**: Handles location variations, typos, and alternative names
- **Web Scraping**: Real-time data from Vietnam National Center for Hydro-Meteorological Forecasting (nchmf.gov.vn)
- **Current Weather**: Temperature, humidity, wind, pressure, visibility, UV index
- **Weather Forecasting**: Multi-period forecasts for today, tomorrow, and day after
- **REST API**: FastAPI endpoints for easy integration
- **Error Handling**: Comprehensive error handling with fallback suggestions
- **Health Monitoring**: Service health checks and status monitoring

## Architecture

```
external_services/weather_service/
├── __init__.py              # Package exports
├── models.py                # Pydantic data models
├── location_mapper.py       # Location to weather station mapping
├── weather_scraper.py       # Web scraping logic
├── weather_service.py       # Main service class
└── vn_stations.json        # Vietnamese weather station data
```

## API Endpoints

### Health Check
```
GET /api/weather/health
```
Returns service status and availability information.

### Location Suggestions
```
GET /api/weather/suggestions?location=<query>
```
Get location suggestions for partial or invalid location queries.

### Weather Data (GET)
```
GET /api/weather?location=<name>&include_forecast=<bool>
```
Retrieve weather data using query parameters.

### Weather Data (POST)
```
POST /api/weather
Content-Type: application/json

{
  "location": "Ho Chi Minh",
  "include_forecast": true,
  "similarity_threshold": 0.6
}
```
Retrieve weather data using JSON payload.

## Usage Examples

### Python Integration

```python
from external_services.weather_service import WeatherService

# Initialize service
weather_service = WeatherService()

# Get weather data
weather_data = await weather_service.get_weather("Ho Chi Minh")

# Get location suggestions
suggestions = weather_service.get_location_suggestions("Hanoi")

# Health check
health_status = await weather_service.health_check()
```

### API Usage

```bash
# Health check
curl http://localhost:8000/api/weather/health

# Location suggestions
curl "http://localhost:8000/api/weather/suggestions?location=Ho Chi"

# Weather data
curl "http://localhost:8000/api/weather?location=Hanoi"

# Weather data (POST)
curl -X POST http://localhost:8000/api/weather \
  -H "Content-Type: application/json" \
  -d '{"location": "Da Nang", "include_forecast": true}'
```

## Data Models

### WeatherData
Complete weather information for a location.

```python
{
  "location": "Sài Gòn (Tp Hồ Chí Minh)",
  "source_url": "https://www.nchmf.gov.vn/kttv/vi-VN/1/sai-gon-tp-ho-chi-minh-w15.html",
  "last_updated": "2025-09-12T16:22:43.191863",
  "current": {
    "temperature_c": 28,
    "humidity_percent": 75,
    "wind_speed_kmh": 15,
    "wind_direction": "NE",
    "condition": "Partly Cloudy",
    "pressure_hpa": 1012,
    "visibility_km": 10,
    "uv_index": 6
  },
  "forecast": {
    "today": [
      {
        "time": "06:00",
        "temperature_c": 24,
        "condition": "Clear",
        "humidity_percent": 80,
        "wind_speed_kmh": 10,
        "wind_direction": "NE"
      }
    ],
    "tomorrow": [...],
    "day_after": [...]
  }
}
```

### WeatherError
Error response for failed requests.

```python
{
  "error": "No weather station found for location: Invalid Location",
  "error_code": "LOCATION_NOT_FOUND",
  "location": "Invalid Location",
  "timestamp": "2025-09-12T16:22:43.191863"
}
```

## Location Mapping

The service supports 63 Vietnamese weather stations including:

- **Major Cities**: Ho Chi Minh City, Hanoi, Da Nang, Can Tho, Hue
- **Provincial Capitals**: All provincial capitals and major districts
- **Location Variations**: Handles multiple names and spellings
- **Fuzzy Matching**: Tolerance for typos and abbreviations

### Supported Location Formats

- Full names: "Ho Chi Minh City", "Thanh pho Ho Chi Minh"
- Short names: "HCMC", "TP HCM", "Sài Gòn"
- Alternative spellings: "Hanoi", "Ha Noi", "Hà Nội"
- Provincial format: "District (Province)"

## Error Handling

The service provides comprehensive error handling:

1. **Location Not Found**: Returns suggestions for similar locations
2. **Network Errors**: Retry mechanism with exponential backoff
3. **Parsing Errors**: Graceful degradation with partial data
4. **Service Unavailable**: Clear error messages and status codes

## Performance

- **Response Time**: Typically 1-3 seconds for weather data retrieval
- **Caching**: Built-in retry mechanism for reliability
- **Concurrency**: Async/await support for multiple concurrent requests
- **Rate Limiting**: Respectful scraping with delays between requests

## Testing

Run the test suite:

```bash
# Quick functionality test
python quick_weather_test.py

# Comprehensive integration test  
python test_integration.py

# API endpoint testing
python test_weather_api.py
```

## Dependencies

- `fastapi`: Web framework for API endpoints
- `pydantic`: Data validation and serialization
- `httpx`: Async HTTP client for web scraping
- `beautifulsoup4`: HTML parsing for weather data extraction
- `lxml`: Fast XML/HTML parser
- `tenacity`: Retry mechanism for reliability

## Integration with AI Chatbot

The weather service is designed as an external tool for the AI chatbot:

1. **Tool Registration**: Register weather endpoints as available tools
2. **Natural Language**: Convert user weather queries to API calls
3. **Response Formatting**: Format weather data for conversational responses
4. **Error Handling**: Provide helpful suggestions when locations aren't found

### Example Chatbot Integration

```python
# In the chatbot's tool registry
weather_tool = {
    "name": "get_weather",
    "description": "Get current weather and forecast for Vietnamese locations",
    "parameters": {
        "location": "Location name in Vietnam",
        "include_forecast": "Whether to include weather forecast"
    },
    "endpoint": "/api/weather"
}
```

## Monitoring and Maintenance

- **Health Checks**: Built-in health monitoring endpoints
- **Logging**: Comprehensive logging throughout all components
- **Error Tracking**: Detailed error information for debugging
- **Station Updates**: Weather station data can be updated in `vn_stations.json`

## Future Enhancements

- **Additional Data Sources**: Support for multiple weather providers
- **Caching Layer**: Redis caching for improved performance
- **Historical Data**: Access to historical weather information
- **Weather Alerts**: Integration with weather warning systems
- **Mobile Optimization**: Optimized responses for mobile applications

## Contributing

When extending the weather service:

1. Follow the existing code structure and patterns
2. Add comprehensive tests for new functionality
3. Update the API documentation
4. Ensure backward compatibility
5. Test with real Vietnamese location queries

## License

This weather service is part of the AgriFinHub Chatbot project and follows the project's licensing terms.
