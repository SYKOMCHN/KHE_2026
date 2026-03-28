import requests
from typing import Dict, Any, Optional
from datetime import datetime
from geopy.geocoders import Nominatim
import time

class WeatherService:
    """Service for fetching weather data from Open-Meteo API and classifying climate regions"""
    
    # Climate region thresholds
    CLIMATE_THRESHOLDS = {
        'desert': {
            'temp_min': 20,
            'humidity_max': 40,
            'precipitation_max': 2.0
        },
        'arctic': {
            'temp_max': 5,
            'precipitation_min': 0
        },
        'tropic': {
            'temp_min': 25,
            'humidity_min': 60,
            'precipitation_min': 10
        },
        'temperate': {
            'temp_min': 5,
            'temp_max': 25,
            'humidity_min': 30,
            'humidity_max': 80,
            'precipitation_max': 50
        }
    }
    
    # Texas cities with their coordinates
    TEXAS_CITIES = {
        'Houston': {'lat': 29.7604, 'lon': -95.3698},
        'Dallas': {'lat': 32.7767, 'lon': -96.7970},
        'San Antonio': {'lat': 29.4241, 'lon': -98.4936},
        'Austin': {'lat': 30.2672, 'lon': -97.7431},
        'Fort Worth': {'lat': 32.7555, 'lon': -97.3308}
    }
    
    def __init__(self):
        """Initialize the weather service"""
        self.base_url = "https://api.open-meteo.com/v1/forecast"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
    
    def get_coordinates(self, city: str, country: str = "United States") -> Optional[Dict[str, float]]:
        """
        Get latitude and longitude for a city
        
        Args:
            city: City name
            country: Country name (default: United States)
            
        Returns:
            Dictionary with 'lat' and 'lon' keys, or None if not found
        """
        try:
            # Use cached coordinates for Texas cities
            if city in self.TEXAS_CITIES:
                return self.TEXAS_CITIES[city]
            
            params = {
                'name': city,
                'country': country,
                'language': 'en',
                'format': 'json'
            }
            response = requests.get(self.geocoding_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results'):
                result = data['results'][0]
                return {'lat': result['latitude'], 'lon': result['longitude']}
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error geocoding {city}: {e}")
            return None
    
    def get_weather_by_city(self, city: str, country_code: str = "US") -> Optional[Dict[str, Any]]:
        """
        Fetch weather data for a specific city
        
        Args:
            city: City name
            country_code: Country code (default: US)
            
        Returns:
            Raw weather data from API or None if failed
        """
        try:
            coords = self.get_coordinates(city, "United States")
            if not coords:
                print(f"Could not find coordinates for {city}")
                return None
            
            params = {
                'latitude': coords['lat'],
                'longitude': coords['lon'],
                'current': 'temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_direction_10m,cloud_cover',
                'timezone': 'auto'
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Add city name and coordinates to response
            data['city'] = city
            data['coordinates'] = coords
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data for {city}: {e}")
            return None
    
    def get_texas_weather_data(self) -> Dict[str, Any]:
        """
        Fetch weather data for multiple major Texas cities
        
        Returns:
            Dictionary with weather data for each city
        """
        weather_data = {}
        
        for city in self.TEXAS_CITIES.keys():
            time.sleep(0.5)  # Rate limiting - be nice to the API
            data = self.get_weather_by_city(city, "US")
            if data:
                weather_data[city] = data
        
        return weather_data
    
    def get_weather_description(self, weather_code: int) -> str:
        """
        Convert WMO weather code to human-readable description
        
        Args:
            weather_code: WMO weather code
            
        Returns:
            Human-readable weather description
        """
        weather_codes = {
            0: 'clear sky',
            1: 'mainly clear',
            2: 'partly cloudy',
            3: 'overcast',
            45: 'foggy',
            48: 'depositing rime fog',
            51: 'light drizzle',
            53: 'moderate drizzle',
            55: 'dense drizzle',
            61: 'slight rain',
            63: 'moderate rain',
            65: 'heavy rain',
            71: 'slight snow',
            73: 'moderate snow',
            75: 'heavy snow',
            77: 'snow grains',
            80: 'slight rain showers',
            81: 'moderate rain showers',
            82: 'violent rain showers',
            85: 'slight snow showers',
            86: 'heavy snow showers',
            95: 'thunderstorm',
            96: 'thunderstorm with slight hail',
            99: 'thunderstorm with heavy hail'
        }
        return weather_codes.get(weather_code, 'unknown')
    
    def classify_region(self, weather_data: Dict[str, Any]) -> str:
        """
        Classify weather conditions into one of four climate regions
        
        Args:
            weather_data: Raw weather data from Open-Meteo API
            
        Returns:
            Climate region classification (desert, arctic, tropic, temperate)
        """
        try:
            current = weather_data.get('current', {})
            temperature = current.get('temperature_2m', 15)
            humidity = current.get('relative_humidity_2m', 50)
            precipitation = current.get('precipitation', 0)
            weather_code = current.get('weather_code', 0)
            description = self.get_weather_description(weather_code).lower()
            
            # Check arctic conditions first (highest priority for cold)
            if temperature <= self.CLIMATE_THRESHOLDS['arctic']['temp_max']:
                if any(cond in description for cond in ['snow', 'ice', 'sleet']):
                    return 'arctic'
            
            # Check desert conditions (hot and dry)
            thresholds = self.CLIMATE_THRESHOLDS['desert']
            if (temperature >= thresholds['temp_min'] and 
                humidity <= thresholds['humidity_max'] and
                precipitation <= thresholds['precipitation_max']):
                if any(cond in description for cond in ['clear', 'sunny', 'mainly clear']):
                    return 'desert'
            
            # Check tropic conditions (warm and humid)
            thresholds = self.CLIMATE_THRESHOLDS['tropic']
            if (temperature >= thresholds['temp_min'] and 
                humidity >= thresholds['humidity_min']):
                if any(cond in description for cond in ['rain', 'thunderstorm', 'drizzle', 'showers']):
                    return 'tropic'
            
            # Default to temperate for moderate conditions
            return 'temperate'
            
        except (KeyError, TypeError) as e:
            print(f"Error classifying weather: {e}")
            return 'temperate'  # Default fallback
    
    def extract_climate_features(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract climate features from weather data
        
        Args:
            weather_data: Raw weather data from Open-Meteo API
            
        Returns:
            Dictionary containing extracted climate features
        """
        try:
            current = weather_data.get('current', {})
            weather_code = current.get('weather_code', 0)
            
            features = {
                'temperature': current.get('temperature_2m', 0),
                'apparent_temperature': current.get('apparent_temperature', 0),
                'humidity': current.get('relative_humidity_2m', 0),
                'precipitation': current.get('precipitation', 0),
                'weather_code': weather_code,
                'weather_description': self.get_weather_description(weather_code),
                'wind_speed': current.get('wind_speed_10m', 0),
                'wind_direction': current.get('wind_direction_10m', 0),
                'cloud_cover': current.get('cloud_cover', 0),
                'timestamp': current.get('time', ''),
                'timezone': weather_data.get('timezone', 'UTC'),
                'elevation': weather_data.get('elevation', 0),
                'coordinates': weather_data.get('coordinates', {})
            }
            
            return features
        except (KeyError, TypeError) as e:
            print(f"Error extracting features: {e}")
            return {}
    
    def process_city_weather(self, city: str) -> Optional[Dict[str, Any]]:
        """
        Process weather data for a city: fetch, extract features, and classify region
        
        Args:
            city: City name
            
        Returns:
            Dictionary containing weather data, features, and region classification
        """
        weather_data = self.get_weather_by_city(city, "US")
        
        if not weather_data:
            return None
        
        features = self.extract_climate_features(weather_data)
        region = self.classify_region(weather_data)
        
        return {
            'city': city,
            'region': region,
            'features': features,
            'raw_data': weather_data
        }
    
    def process_texas_weather(self) -> Dict[str, Any]:
        """
        Process weather data for all major Texas cities
        
        Returns:
            Dictionary with processed weather data, features, and region classifications
        """
        all_city_data = {}
        region_summary = {
            'desert': [],
            'arctic': [],
            'tropic': [],
            'temperate': []
        }
        
        for city in self.TEXAS_CITIES.keys():
            time.sleep(0.5)  # Rate limiting
            processed = self.process_city_weather(city)
            
            if processed:
                all_city_data[city] = processed
                region = processed['region']
                region_summary[region].append(city)
        
        return {
            'cities': all_city_data,
            'summary': region_summary,
            'total_cities': len(all_city_data),
            'processed_at': datetime.now().isoformat()
        }


# Convenience function for initialization
def get_weather_service() -> WeatherService:
    """Create and return a WeatherService instance"""
    return WeatherService()
