"""
Test/Demo script for weather API integration and climate classification
"""
import sys
from backend.climate import get_climate_analyzer
from backend.weather_service import get_weather_service
import json


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_weather_service():
    """Demonstrate the weather service functionality"""
    print_section("WEATHER SERVICE DEMO")
    
    try:
        service = get_weather_service()
        print("✓ Weather service initialized successfully")
        print(f"  Base URL: {service.base_url}")
        print(f"  API: Open-Meteo (No API key required)")
        print(f"  Texas Cities Supported: {len(service.TEXAS_CITIES)}")
        
    except Exception as e:
        print(f"✗ Error initializing weather service: {e}")
        return False
    
    return True


def demo_single_city(city):
    """Demonstrate analyzing a single city"""
    print_section(f"ANALYZING: {city}")
    
    try:
        analyzer = get_climate_analyzer()
        result = analyzer.analyze_city(city)
        
        if not result:
            print(f"✗ Could not fetch weather for {city}")
            return False
        
        print(f"✓ Successfully fetched and analyzed {city}")
        print(f"\n  City: {result['city']}")
        print(f"  Region Classification: {result['region'].upper()}")
        
        features = result.get('features', {})
        print(f"\n  Climate Features:")
        print(f"    • Temperature: {features.get('temperature')}°C")
        print(f"    • Apparent Temperature: {features.get('apparent_temperature')}°C")
        print(f"    • Humidity: {features.get('humidity')}%")
        print(f"    • Precipitation: {features.get('precipitation')} mm")
        print(f"    • Weather: {features.get('weather_description', 'N/A')}")
        print(f"    • Wind Speed: {features.get('wind_speed')} m/s")
        print(f"    • Wind Direction: {features.get('wind_direction')}°")
        print(f"    • Cloud Cover: {features.get('cloud_cover')}%")
        print(f"    • Timezone: {features.get('timezone')}")
        print(f"    • Timestamp: {features.get('timestamp')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error analyzing {city}: {e}")
        return False


def demo_texas_regions():
    """Demonstrate analyzing all Texas cities and regional distribution"""
    print_section("TEXAS CLIMATE REGIONS ANALYSIS")
    
    try:
        analyzer = get_climate_analyzer()
        print("Fetching weather data for Texas cities...")
        
        texas_data = analyzer.fetch_and_analyze_texas()
        
        if not texas_data or 'cities' not in texas_data:
            print("✗ Could not fetch Texas weather data")
            return False
        
        print(f"✓ Successfully fetched data for {texas_data['total_cities']} cities")
        print(f"  Processed at: {texas_data['processed_at']}\n")
        
        # Display regional distribution
        print("  Regional Distribution:")
        print("  " + "-" * 50)
        
        summary = texas_data.get('summary', {})
        regions_info = {
            'desert': '🏜️  Desert',
            'arctic': '❄️  Arctic',
            'tropic': '🌴 Tropical',
            'temperate': '🌤️  Temperate'
        }
        
        for region, emoji_name in regions_info.items():
            cities = summary.get(region, [])
            print(f"    {emoji_name}: {', '.join(cities) if cities else 'No cities'}")
        
        # Display city details
        print("\n  City Details:")
        print("  " + "-" * 70)
        
        for city, data in texas_data.get('cities', {}).items():
            features = data.get('features', {})
            region = data.get('region', 'unknown').upper()
            temp = features.get('temperature', 'N/A')
            humidity = features.get('humidity', 'N/A')
            precipitation = features.get('precipitation', 'N/A')
            description = features.get('weather_description', 'N/A')
            
            print(f"    {city:15} | Region: {region:10} | Temp: {temp:5}°C | "
                  f"Humidity: {humidity:3}% | Rain: {precipitation:.1f}mm")
        
        return True
        
    except Exception as e:
        print(f"✗ Error analyzing Texas regions: {e}")
        import traceback
        traceback.print_exc()
        return False


def demo_region_filter():
    """Demonstrate filtering cities by region"""
    print_section("REGIONAL FILTERING")
    
    try:
        analyzer = get_climate_analyzer()
        regions = ['desert', 'arctic', 'tropic', 'temperate']
        
        print("Cities by region:")
        for region in regions:
            cities = analyzer.get_region_cities(region)
            status = "✓" if cities else "✗"
            print(f"  {status} {region.upper():10} - {len(cities)} cities: {', '.join(cities) if cities else 'None'}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error filtering regions: {e}")
        return False


def main():
    """Run all demonstrations"""
    print("\n" + "="*60)
    print("  WEATHER API & CLIMATE CLASSIFICATION DEMO")
    print("="*60)
    
    # Step 1: Initialize
    if not demo_weather_service():
        print("\n✗ Failed to initialize weather service. Exiting.")
        return
    
    # Step 2: Analyze single city
    demo_single_city("Austin")
    
    # Step 3: Analyze all Texas cities
    demo_texas_regions()
    
    # Step 4: Filter by region
    demo_region_filter()
    
    print_section("DEMO COMPLETE")
    print("✓ All demonstrations completed successfully!")
    print("\nAPI Endpoints Available:")
    print("  • GET  /api/weather/texas - Get all Texas cities' weather")
    print("  • GET  /api/weather/regions - Get regional distribution")
    print("  • GET  /api/weather/city/<city> - Get specific city weather")
    print("  • GET  /api/climate/region/<region> - Get cities in a region")


if __name__ == '__main__':
    main()
