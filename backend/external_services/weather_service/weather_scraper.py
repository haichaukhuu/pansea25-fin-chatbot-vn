import asyncio
import re
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from urllib.parse import urljoin
import time

import httpx
from bs4 import BeautifulSoup, Tag
from tenacity import retry, stop_after_attempt, wait_exponential

try:
    from .models import WeatherData, CurrentWeather, WeatherForecast, ForecastPeriod
except ImportError:
    from models import WeatherData, CurrentWeather, WeatherForecast, ForecastPeriod

logger = logging.getLogger(__name__)


class WeatherScraper:    
    def __init__(self, timeout: int = 30, retries: int = 3):
        self.timeout = timeout
        self.retries = retries
        self.session = None
        
        # Common headers to mimic browser requests
        self.headers = {
            'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/91.0.4472.124 Safari/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(
            timeout=self.timeout,
            headers=self.headers,
            follow_redirects=True
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def _fetch_page(self, url: str) -> str:
        """Fetch webpage content with retry logic.
        """
        if not self.session:
            raise RuntimeError("Scraper not initialized. Use async context manager.")
        
        logger.info(f"Fetching weather data from: {url}")
        
        try:
            response = await self.session.get(url)
            response.raise_for_status()
            
            # Check if we got a valid response
            if len(response.content) < 100:
                raise httpx.HTTPError(f"Response too short: {len(response.content)} bytes")
            
            return response.text
            
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching {url}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching {url}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            raise httpx.HTTPError(f"Unexpected error: {e}")
    
    def _parse_temperature(self, text: str) -> Optional[int]:
        """Parse temperature from text - enhanced for Vietnamese.
        """
        if not text:
            return None
        
        # Enhanced temperature patterns for Vietnamese
        temp_patterns = [
            r'(\d+)°C',
            r'(\d+)°',
            r'(\d+)\s*độ\s*C',
            r'(\d+)\s*độ',
            r'(\d+)\s*°C',
            r'(\d+)\s*°',
            r'nhiệt\s*độ\s*:\s*(\d+)',
            r'temp\s*:\s*(\d+)',
            r'(\d+)\s*degrees?',
        ]
        
        # Clean the text first
        text = text.strip()
        
        for pattern in temp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    temp = int(match.group(1))
                    # Validate reasonable temperature range (-50 to 60°C)
                    if -50 <= temp <= 60:
                        return temp
                except ValueError:
                    continue
        
        return None
    
    def _parse_humidity(self, text: str) -> Optional[int]:
        """Parse humidity percentage from text."""
        if not text:
            return None
        
        # Look for humidity patterns like "75%", "75 %"
        humidity_patterns = [
            r'(\d+)%',
            r'(\d+)\s*%',
            r'độ\s*ẩm\s*:\s*(\d+)',
        ]
        
        for pattern in humidity_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    humidity = int(match.group(1))
                    if 0 <= humidity <= 100:
                        return humidity
                except ValueError:
                    continue
        
        return None
    
    def _parse_wind_speed(self, text: str) -> Optional[int]:
        """Parse wind speed from text - enhanced for Vietnamese."""
        if not text:
            return None
        
        # Look for wind speed patterns (including Vietnamese patterns)
        wind_patterns = [
            r'(\d+)\s*km/h',
            r'(\d+)\s*m/s',
            r'tốc\s*độ\s*:\s*(\d+)',
            r'gió\s*:\s*(\d+)',
            r'(\d+)\s*km/giờ',
        ]
        
        for pattern in wind_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    speed = int(match.group(1))
                    # Convert m/s to km/h if needed
                    if 'm/s' in text.lower():
                        speed = int(speed * 3.6)
                    return speed
                except ValueError:
                    continue
        
        return None
    
    def _parse_wind_direction(self, text: str) -> Optional[str]:
        """Parse wind direction from text - enhanced for Vietnamese."""
        if not text:
            return None
        
        # Enhanced Vietnamese wind direction mappings
        direction_map = {
            'bắc': 'North',
            'nam': 'South', 
            'đông': 'East',
            'tây': 'West',
            'đông bắc': 'Northeast',
            'tây bắc': 'Northwest',
            'đông nam': 'Southeast',
            'tây nam': 'Southwest',
            'lặng gió': 'Calm',
            'gió nhẹ': 'Light',
            'gió mạnh': 'Strong',
            'north': 'North',
            'south': 'South',
            'east': 'East',
            'west': 'West',
            'northeast': 'Northeast',
            'northwest': 'Northwest',
            'southeast': 'Southeast',
            'southwest': 'Southwest',
        }
        
        text_lower = text.lower()
        for vietnamese, english in direction_map.items():
            if vietnamese in text_lower:
                return english
        
        return None
    
    def _extract_current_weather(self, soup: BeautifulSoup, url: str) -> Optional[CurrentWeather]:
        """Extract current weather conditions from parsed HTML.
        """
        try:
            current_weather = CurrentWeather()
            
            # Look for current weather section
            current_sections = soup.find_all(['div', 'section', 'table'], 
                                           class_=re.compile(r'current|hiện.tại|weather', re.I))
            
            if not current_sections:
                # Fallback: look for any section containing current weather indicators
                current_sections = soup.find_all(text=re.compile(r'thời tiết hiện tại|current|cập nhật', re.I))
                if current_sections:
                    current_sections = [elem.parent for elem in current_sections if elem.parent]
            
            if not current_sections:
                logger.warning(f"No current weather section found in {url}")
                return None
            
            # Process the first current weather section found
            current_section = current_sections[0]
            if isinstance(current_section, Tag):
                section_text = current_section.get_text()
                
                # Extract temperature
                current_weather.temperature_c = self._parse_temperature(section_text)
                
                # Extract humidity
                current_weather.humidity_percent = self._parse_humidity(section_text)
                
                # Extract wind speed
                current_weather.wind_speed_kmh = self._parse_wind_speed(section_text)
                
                # Extract wind direction
                current_weather.wind_direction = self._parse_wind_direction(section_text)
                
                # Extract weather condition
                condition_keywords = ['thời tiết', 'condition', 'tình trạng']
                for keyword in condition_keywords:
                    condition_elem = current_section.find(text=re.compile(keyword, re.I))
                    if condition_elem and condition_elem.parent:
                        condition_text = condition_elem.parent.get_text().strip()
                        # Clean up the condition text
                        condition_text = re.sub(r'thời tiết\s*:\s*', '', condition_text, flags=re.I)
                        if condition_text and len(condition_text) < 100:
                            current_weather.condition = condition_text
                            break
            
            # Return current weather if we found at least temperature
            if current_weather.temperature_c is not None:
                return current_weather
            
            logger.warning(f"Could not extract meaningful current weather data from {url}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting current weather from {url}: {e}")
            return None
    
    def _extract_forecast(self, soup: BeautifulSoup, url: str) -> Optional[WeatherForecast]:
        """Extract weather forecast from parsed HTML - enhanced for Vietnamese weather sites.
        """
        try:
            forecast = WeatherForecast()
            
            # Enhanced Vietnamese weather site parsing
            logger.info(f"Extracting 10-day forecast from Vietnamese weather site")
            
            # Look for Vietnamese weather forecast sections with specific patterns
            forecast_sections = []
            
            # Primary: Look for ten-days-weather class (specific to Vietnamese weather site)
            ten_days_sections = soup.find_all('div', class_='ten-days-weather')
            if ten_days_sections:
                forecast_sections.extend(ten_days_sections)
                logger.info(f"Found {len(ten_days_sections)} ten-days-weather sections")
            
            # Secondary: Look for generic forecast patterns
            if not forecast_sections:
                forecast_sections = soup.find_all(['div', 'section', 'table'],
                                                class_=re.compile(r'forecast|dự.báo|10.ngày', re.I))
                
            if not forecast_sections:
                logger.warning(f"No forecast section found in {url}")
                return WeatherForecast()  # Return empty forecast instead of None
            
            # Process Vietnamese forecast data
            for section in forecast_sections:
                if isinstance(section, Tag):
                    # Look for item-days-wt class elements (Vietnamese weather site structure)
                    day_items = section.find_all('div', class_='item-days-wt')
                    
                    if day_items:
                        logger.info(f"Found {len(day_items)} forecast items using Vietnamese structure")
                        
                        for i, item in enumerate(day_items):
                            try:
                                # Extract Vietnamese date text
                                date_elem = item.find('p', class_='text-days')
                                date_text = date_elem.get_text(strip=True) if date_elem else f"Day {i+1}"
                                
                                # Extract high temperature
                                high_temp = None
                                large_temp_elem = item.find('span', class_='large-temp')
                                if large_temp_elem:
                                    high_temp = self._parse_temperature(large_temp_elem.get_text())
                                
                                # Extract low temperature  
                                low_temp = None
                                small_temp_elem = item.find('span', class_='small-temp')
                                if small_temp_elem:
                                    low_temp = self._parse_temperature(small_temp_elem.get_text())
                                
                                # Calculate average temperature
                                avg_temp = None
                                if high_temp is not None and low_temp is not None:
                                    avg_temp = (high_temp + low_temp) // 2
                                elif high_temp is not None:
                                    avg_temp = high_temp
                                elif low_temp is not None:
                                    avg_temp = low_temp
                                
                                # Extract weather condition
                                condition = None
                                text_temp_elem = item.find('p', class_='text-temp')
                                if text_temp_elem:
                                    condition = text_temp_elem.get_text(strip=True)
                                
                                # Extract wind information
                                wind_speed = None
                                wind_direction = None
                                wind_elem = item.find('p', class_='wind-info')
                                if wind_elem:
                                    wind_text = wind_elem.get_text(strip=True)
                                    wind_speed = self._parse_wind_speed(wind_text)
                                    wind_direction = self._parse_wind_direction(wind_text)
                                
                                # Create forecast period with Vietnamese date format
                                period = ForecastPeriod(
                                    time=date_text,
                                    temperature_c=avg_temp,
                                    condition=condition,
                                    wind_speed_kmh=wind_speed,
                                    wind_direction=wind_direction
                                )
                                
                                # Assign to appropriate day (first 3 days)
                                if i == 0:
                                    forecast.today.append(period)
                                elif i == 1:
                                    forecast.tomorrow.append(period)
                                elif i == 2:
                                    forecast.day_after.append(period)
                                
                                logger.debug(f"Parsed forecast item {i}: {date_text}, {avg_temp}°C, {condition}")
                                
                            except Exception as item_error:
                                logger.warning(f"Error parsing forecast item {i}: {item_error}")
                                continue
                                
                        # If we found Vietnamese structure data, return it
                        if forecast.today or forecast.tomorrow or forecast.day_after:
                            logger.info(f"Successfully extracted Vietnamese forecast data")
                            return forecast
                    
                    # Fallback: Generic parsing for non-Vietnamese sites
                    else:
                        logger.info("Using fallback generic forecast parsing")
                        day_entries = section.find_all(['tr', 'div'], 
                                                     class_=re.compile(r'day|ngày|date', re.I))
                        
                        if not day_entries:
                            day_entries = section.find_all(['tr', 'div'])
                        
                        for i, entry in enumerate(day_entries[:3]):  # Process first 3 days
                            if isinstance(entry, Tag):
                                entry_text = entry.get_text()
                                
                                # Create forecast period
                                period = ForecastPeriod(
                                    time=f"Day {i+1}",
                                    temperature_c=self._parse_temperature(entry_text),
                                    condition=self._extract_condition_from_text(entry_text),
                                    humidity_percent=self._parse_humidity(entry_text),
                                    wind_speed_kmh=self._parse_wind_speed(entry_text)
                                )
                                
                                # Assign to appropriate day
                                if i == 0:
                                    forecast.today.append(period)
                                elif i == 1:
                                    forecast.tomorrow.append(period)
                                elif i == 2:
                                    forecast.day_after.append(period)
            
            # Return forecast (may be empty but not None for robust error handling)
            if forecast.today or forecast.tomorrow or forecast.day_after:
                logger.info(f"Successfully extracted forecast data: today={len(forecast.today)}, tomorrow={len(forecast.tomorrow)}, day_after={len(forecast.day_after)}")
            else:
                logger.warning(f"Could not extract meaningful forecast data from {url}")
            
            return forecast
            
        except Exception as e:
            logger.error(f"Error extracting forecast from {url}: {e}")
            return WeatherForecast()  # Return empty forecast instead of None
    
    def _extract_condition_from_text(self, text: str) -> Optional[str]:
        """Extract weather condition from text - enhanced for Vietnamese."""
        if not text:
            return None
        
        # Enhanced Vietnamese weather conditions
        conditions = [
            'nắng', 'mưa', 'mây', 'sương mù', 'gió', 'bão', 'dông',
            'có mây', 'ít mây', 'nhiều mây', 'trời nắng', 'mưa rão',
            'mưa dông', 'sương', 'khô hanh', 'nắng nóng', 'nắng gắt',
            'có mây, không mưa', 'có mây, có mưa', 'mưa vừa', 'mưa to',
            'mưa nhỏ', 'nắng ít mây', 'nhiều mây, có mưa', 'âm u',
            'quang mây', 'nắng hanh', 'lạnh', 'mát mẻ'
        ]
        
        text_lower = text.lower().strip()
        
        # First, try to find exact matches for longer conditions
        longer_conditions = [c for c in conditions if len(c) > 5]
        longer_conditions.sort(key=len, reverse=True)  # Sort by length, longest first
        
        for condition in longer_conditions:
            if condition in text_lower:
                # Return the original condition text cleaned up
                return text.strip()
        
        # Then try shorter conditions
        for condition in conditions:
            if condition in text_lower:
                # Extract the sentence containing the condition
                sentences = text.split('.')
                for sentence in sentences:
                    if condition in sentence.lower():
                        cleaned = sentence.strip()
                        if cleaned:
                            return cleaned
                # If no sentence found, return the original text
                return text.strip()
        
        # If no Vietnamese conditions found, return original text if it looks like a condition
        if len(text.strip()) < 50 and any(word in text_lower for word in ['sunny', 'cloudy', 'rain', 'clear', 'fog']):
            return text.strip()
        
        return None
    
    async def scrape_weather(self, url: str, location: str) -> WeatherData:
        """Scrape weather data from a given URL."""
        try:
            # Fetch the webpage
            html_content = await self._fetch_page(url)
            
            # Parse HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract current weather
            current_weather = self._extract_current_weather(soup, url)
            
            # Extract forecast
            forecast = self._extract_forecast(soup, url)
            
            # Create weather data object
            weather_data = WeatherData(
                location=location,
                source_url=url,
                last_updated=datetime.now(),
                current=current_weather,
                forecast=forecast
            )
            
            logger.info(f"Successfully scraped weather data for {location}")
            return weather_data
            
        except Exception as e:
            logger.error(f"Failed to scrape weather data from {url}: {e}")
            raise
    
    def scrape_weather_sync(self, url: str, location: str) -> WeatherData:
        """Synchronous wrapper for scrape_weather."""
        async def _scrape():
            async with self:
                return await self.scrape_weather(url, location)
        
        return asyncio.run(_scrape())
