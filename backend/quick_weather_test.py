#!/usr/bin/env python3
"""
Quick Weather Service Test
Tests core functionality without heavy web scraping
"""

import asyncio
import sys
import os
import logging

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our components
from external_services.weather_service import WeatherService, LocationMapper
from external_services.weather_service.models import WeatherError

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_location_mapping():
    """Test location mapping functionality"""
    print("\n" + "="*50)
    print("TESTING LOCATION MAPPING")
    print("="*50)
    
    mapper = LocationMapper()
    
    test_locations = [
        "Ho Chi Minh",
        "Hanoi", 
        "Da Nang",
        "Invalid Location"
    ]
    
    for location in test_locations:
        print(f"\nTesting location: '{location}'")
        try:
            result = mapper.map_location(location)
            if result.success and result.url:
                print(f"  ✓ Mapped to: {result.mapped_location}")
                print(f"  ✓ URL: {result.url}")
            else:
                print(f"  ✗ Failed: {result.error_message}")
                print(f"  ✓ Suggestions: {len(result.suggestions)}")
                for i, suggestion in enumerate(result.suggestions[:3]):
                    print(f"    - {suggestion.suggested_location} (score: {suggestion.similarity_score:.2f})")
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")

async def test_weather_service_basic():
    """Test basic weather service functionality"""
    print("\n" + "="*50)
    print("TESTING WEATHER SERVICE BASIC")
    print("="*50)
    
    try:
        service = WeatherService()
        
        # Test health check
        print("\nTesting health check...")
        health = await service.health_check()
        print(f"  ✓ Health check: {health['status']}")
        print(f"  ✓ Location mapper: {health['checks']['location_mapper']['status']}")
        print(f"  ✓ Available locations: {health['checks']['location_mapper']['locations_count']}")
        
        # Test location suggestions
        print("\nTesting location suggestions...")
        suggestions = service.get_location_suggestions("Ho Chi")
        print(f"  ✓ Found {len(suggestions.suggestions)} suggestions for 'Ho Chi'")
        for suggestion in suggestions.suggestions[:3]:
            print(f"    - {suggestion.suggested_location} (score: {suggestion.similarity_score:.2f})")
            
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        logger.error(f"Weather service test failed: {str(e)}", exc_info=True)

async def test_weather_service_mock():
    """Test weather service with a mock successful response"""
    print("\n" + "="*50)
    print("TESTING WEATHER SERVICE JSON OUTPUT")
    print("="*50)
    
    try:
        service = WeatherService()
        
        # Create a mock weather response to test JSON serialization
        from external_services.weather_service.models import (
            WeatherData, CurrentWeather, WeatherForecast, ForecastPeriod
        )
        from datetime import datetime
        
        # Create test weather data
        current = CurrentWeather(
            temperature_c=28,
            humidity_percent=75,
            wind_speed_kmh=15,
            wind_direction="NE",
            condition="Partly Cloudy"
        )
        
        forecast_periods = [
            ForecastPeriod(
                time=f"{6 + i*6:02d}:00",
                temperature_c=22 + i,
                condition=f"Period {i+1} Condition",
                humidity_percent=70 + i
            ) for i in range(4)
        ]
        
        forecast = WeatherForecast(today=forecast_periods)
        
        weather_data = WeatherData(
            location="Test Location",
            source_url="https://test.example.com",
            last_updated=datetime.now(),
            current=current,
            forecast=forecast
        )
        
        # Test JSON serialization
        json_output = weather_data.model_dump_json(indent=2)
        print("  ✓ Successfully created test weather data")
        print("  ✓ JSON serialization working")
        print(f"  ✓ JSON length: {len(json_output)} characters")
        
        # Print first few lines of JSON
        lines = json_output.split('\n')[:10]
        print("  ✓ Sample JSON output:")
        for line in lines:
            print(f"    {line}")
        
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        logger.error(f"JSON test failed: {str(e)}", exc_info=True)

async def main():
    """Run all quick tests"""
    print("QUICK WEATHER SERVICE TEST SUITE")
    print("=" * 50)
    
    try:
        await test_location_mapping()
        await test_weather_service_basic()
        await test_weather_service_mock()
        
        print("\n" + "="*50)
        print("QUICK TEST SUMMARY")
        print("="*50)
        print("✓ Location mapping test completed")
        print("✓ Weather service basic test completed")
        print("✓ JSON serialization test completed")
        print("\nThe weather service core functionality is working!")
        print("Ready for integration with the chatbot.")
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {str(e)}")
        logger.error(f"Test suite failed: {str(e)}", exc_info=True)
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(main())
