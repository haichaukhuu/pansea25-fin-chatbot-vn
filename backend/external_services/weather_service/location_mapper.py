import json
import os
from typing import Dict, List, Optional
from difflib import SequenceMatcher
import re
import logging

try:
    from .models import LocationMappingResult, LocationSuggestion
except ImportError:
    from models import LocationMappingResult, LocationSuggestion

logger = logging.getLogger(__name__)


class LocationMapper:
    """Maps user location queries to Vietnamese weather station URLs."""
    
    def __init__(self, stations_file: Optional[str] = None):
        self.stations_file = stations_file or self._get_default_stations_file()
        self.stations: Dict[str, str] = {}
        self.location_variations: Dict[str, List[str]] = {}
        self._load_stations()
        self._build_location_variations()
    
    def _get_default_stations_file(self) -> str:
        """Get the default path to the weather stations file."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "vn_stations.json")
    
    def _load_stations(self) -> None:
        """Load weather stations from JSON file."""
        try:
            with open(self.stations_file, 'r', encoding='utf-8') as f:
                self.stations = json.load(f)
            logger.info(f"Loaded {len(self.stations)} weather stations")
        except FileNotFoundError:
            logger.error(f"Weather stations file not found: {self.stations_file}")
            self.stations = {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in stations file: {e}")
            self.stations = {}
        except Exception as e:
            logger.error(f"Error loading weather stations: {e}")
            self.stations = {}
    
    def _build_location_variations(self) -> None:
        """Build a mapping of location variations for better matching."""
        self.location_variations = {}
        
        for station_name in self.stations.keys():
            # Extract base location name and province
            variations = self._extract_location_variations(station_name)
            
            for variation in variations:
                if variation not in self.location_variations:
                    self.location_variations[variation] = []
                self.location_variations[variation].append(station_name)
    
    def _extract_location_variations(self, station_name: str) -> List[str]:
        """Extract possible variations of a location name.
        """
        variations = [station_name.lower()]
        
        # Extract city name before parentheses
        if '(' in station_name:
            city_name = station_name.split('(')[0].strip().lower()
            variations.append(city_name)
            
            # Extract province name from parentheses
            province_match = re.search(r'\(([^)]+)\)', station_name)
            if province_match:
                province = province_match.group(1).strip().lower()
                variations.append(province)
                
                # Handle special cases like "Tp Hồ Chí Minh" -> "Ho Chi Minh"
                if 'tp ' in province:
                    clean_province = province.replace('tp ', '').strip()
                    variations.append(clean_province)
        
        # Remove common prefixes/suffixes and add variations
        for variation in variations.copy():
            # Remove accents for better matching (simplified approach)
            ascii_variation = self._remove_vietnamese_accents(variation)
            if ascii_variation != variation:
                variations.append(ascii_variation)
            
            # Add variations without common words
            for common_word in ['thành phố', 'tp', 'quận', 'huyện', 'xã']:
                if common_word in variation:
                    clean_variation = variation.replace(common_word, '').strip()
                    if clean_variation and clean_variation not in variations:
                        variations.append(clean_variation)
        
        return list(set(variations))
    
    def _remove_vietnamese_accents(self, text: str) -> str:
        """Remove Vietnamese accents for ASCII matching.
        """
        accent_map = {
            'à': 'a', 'á': 'a', 'ạ': 'a', 'ả': 'a', 'ã': 'a',
            'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ậ': 'a', 'ẩ': 'a', 'ẫ': 'a',
            'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ặ': 'a', 'ẳ': 'a', 'ẵ': 'a',
            'è': 'e', 'é': 'e', 'ẹ': 'e', 'ẻ': 'e', 'ẽ': 'e',
            'ê': 'e', 'ề': 'e', 'ế': 'e', 'ệ': 'e', 'ể': 'e', 'ễ': 'e',
            'ì': 'i', 'í': 'i', 'ị': 'i', 'ỉ': 'i', 'ĩ': 'i',
            'ò': 'o', 'ó': 'o', 'ọ': 'o', 'ỏ': 'o', 'õ': 'o',
            'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ộ': 'o', 'ổ': 'o', 'ỗ': 'o',
            'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ợ': 'o', 'ở': 'o', 'ỡ': 'o',
            'ù': 'u', 'ú': 'u', 'ụ': 'u', 'ủ': 'u', 'ũ': 'u',
            'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ự': 'u', 'ử': 'u', 'ữ': 'u',
            'ỳ': 'y', 'ý': 'y', 'ỵ': 'y', 'ỷ': 'y', 'ỹ': 'y',
            'đ': 'd'
        }
        
        result = text.lower()
        for accented, plain in accent_map.items():
            result = result.replace(accented, plain)
        
        return result
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings."""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def map_location(self, user_location: str, threshold: float = 0.6) -> LocationMappingResult:
        """Map user location query to weather station.
        """
        if not user_location or not user_location.strip():
            return LocationMappingResult(
                success=False,
                error_message="Location cannot be empty"
            )
        
        user_location = user_location.strip()
        logger.info(f"Mapping location: {user_location}")
        
        # Try exact match first
        exact_match = self._find_exact_match(user_location)
        if exact_match:
            return LocationMappingResult(
                success=True,
                mapped_location=exact_match,
                url=self.stations[exact_match]
            )
        
        # Try fuzzy matching
        fuzzy_matches = self._find_fuzzy_matches(user_location, threshold)
        
        if fuzzy_matches:
            # Return best match
            best_match = fuzzy_matches[0]
            suggestions = [
                LocationSuggestion(
                    suggested_location=match['station'],
                    similarity_score=match['score'],
                    url=self.stations[match['station']]
                )
                for match in fuzzy_matches[1:5]  # Top 5 suggestions
            ]
            
            return LocationMappingResult(
                success=True,
                mapped_location=best_match['station'],
                url=self.stations[best_match['station']],
                suggestions=suggestions
            )
        
        # No matches found
        return LocationMappingResult(
            success=False,
            error_message=f"No weather station found for location: {user_location}",
            suggestions=self._get_popular_suggestions()
        )
    
    def _find_exact_match(self, user_location: str) -> Optional[str]:
        """Find exact match for user location."""
        user_location_lower = user_location.lower()
        
        # Check direct match in stations
        for station_name in self.stations.keys():
            if station_name.lower() == user_location_lower:
                return station_name
        
        # Check variations
        for variation, stations in self.location_variations.items():
            if variation == user_location_lower:
                return stations[0]  # Return first station for this variation
        
        return None
    
    def _find_fuzzy_matches(self, user_location: str, threshold: float) -> List[Dict]:
        """Find fuzzy matches for user location."""
        matches = []
        user_location_lower = user_location.lower()
        user_location_ascii = self._remove_vietnamese_accents(user_location_lower)
        
        # Check similarity with all station names and variations
        checked_stations = set()
        
        for station_name in self.stations.keys():
            if station_name in checked_stations:
                continue
            
            # Check direct similarity
            similarity = self._calculate_similarity(user_location_lower, station_name.lower())
            if similarity >= threshold:
                matches.append({
                    'station': station_name,
                    'score': similarity,
                    'match_type': 'direct'
                })
                checked_stations.add(station_name)
                continue
            
            # Check similarity with variations
            variations = self._extract_location_variations(station_name)
            max_variation_similarity = 0
            
            for variation in variations:
                var_similarity = self._calculate_similarity(user_location_lower, variation)
                ascii_similarity = self._calculate_similarity(user_location_ascii, 
                                                            self._remove_vietnamese_accents(variation))
                
                max_variation_similarity = max(max_variation_similarity, 
                                             var_similarity, ascii_similarity)
            
            if max_variation_similarity >= threshold:
                matches.append({
                    'station': station_name,
                    'score': max_variation_similarity,
                    'match_type': 'variation'
                })
                checked_stations.add(station_name)
        
        # Sort by similarity score (descending)
        matches.sort(key=lambda x: x['score'], reverse=True)
        return matches
    
    def _get_popular_suggestions(self) -> List[LocationSuggestion]:
        """Get popular/common location suggestions."""
        popular_locations = [
            "Sài Gòn (Tp Hồ Chí Minh)",
            "Hoàn Kiếm (Tp Hà Nội)", 
            "Hải Châu (Tp Đà Nẵng)",
            "Nha Trang (Khánh Hòa)",
            "Lê Chân (Tp Hải Phòng)"
        ]
        
        suggestions = []
        for location in popular_locations:
            if location in self.stations:
                suggestions.append(LocationSuggestion(
                    suggested_location=location,
                    similarity_score=0.0,
                    url=self.stations[location]
                ))
        
        return suggestions
    
    def get_all_locations(self) -> List[str]:
        """Get list of all available weather station locations."""
        return list(self.stations.keys())
    
    def get_location_url(self, location: str) -> Optional[str]:
        """Get weather URL for a specific location."""
        return self.stations.get(location)
