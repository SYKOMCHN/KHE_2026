"""
Climate module for weather data processing and climate region classification
"""
from .weather_service import WeatherService, get_weather_service
from typing import Dict, Any, List, Optional


class ClimateAnalyzer:
    """Analyzes weather data and manages climate region classifications"""
    
    def __init__(self):
        """Initialize the climate analyzer with weather service"""
        self.weather_service = get_weather_service()
        self.region_data = {}
    
    def fetch_and_analyze_texas(self) -> Dict[str, Any]:
        """
        Fetch weather data for Texas and analyze climate regions
        
        Returns:
            Processed weather data with climate classifications
        """
        texas_data = self.weather_service.process_texas_weather()
        self.region_data = texas_data
        return texas_data
    
    def get_region_distribution(self) -> Dict[str, List[str]]:
        """
        Get distribution of cities by climate region
        
        Returns:
            Dictionary mapping regions to city lists
        """
        if not self.region_data:
            return {'error': 'No data available. Run fetch_and_analyze_texas() first.'}
        
        return self.region_data.get('summary', {})
    
    def get_city_details(self, city: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed climate information for a specific city
        
        Args:
            city: City name
            
        Returns:
            City's weather data and classification
        """
        if not self.region_data:
            return None
        
        return self.region_data.get('cities', {}).get(city)
    
    def get_region_cities(self, region: str) -> List[str]:
        """
        Get all cities in a specific climate region
        
        Args:
            region: Climate region name (desert, arctic, tropic, temperate)
            
        Returns:
            List of cities in that region
        """
        if not self.region_data:
            return []
        
        return self.region_data.get('summary', {}).get(region, [])
    
    def analyze_city(self, city: str) -> Optional[Dict[str, Any]]:
        """
        Analyze weather for a single city
        
        Args:
            city: City name
            
        Returns:
            Processed weather data and region classification
        """
        return self.weather_service.process_city_weather(city)


# Initialize a global climate analyzer instance
_climate_analyzer = None


def get_climate_analyzer() -> ClimateAnalyzer:
    """Get or create the global climate analyzer instance"""
    global _climate_analyzer
    if _climate_analyzer is None:
        _climate_analyzer = ClimateAnalyzer()
    return _climate_analyzer



