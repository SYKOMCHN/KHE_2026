**Response:**
```json
{
  "success": true,
  "data": {
    "cities": {
      "Austin": {
        "city": "Austin",
        "region": "temperate",
        "features": {
          "temperature": 22.5,
          "humidity": 65,
          "weather_description": "partly cloudy",
          ...
        }
      },
      ...
    },
    "summary": {
      "desert": ["Phoenix"],
      "arctic": [],
      "tropic": ["Houston"],
      "temperate": ["Austin", "Dallas"]
    }
  }
}
```

### 2. Get Regional Distribution
```
GET /api/weather/regions
```
Returns summary of cities grouped by climate region.

**Response:**
```json
{
  "success": true,
  "regions": {
    "desert": ["Phoenix"],
    "arctic": [],
    "tropic": ["Houston"],
    "temperate": ["Austin", "Dallas", "San Antonio", "Fort Worth"]
  }
}
```

### 3. Get Specific City Weather
```
GET /api/weather/city/<city>
```
Returns detailed weather and climate data for a specific city.

**Example:** `GET /api/weather/city/Austin`

### 4. Get Cities in a Region
```
GET /api/climate/region/<region>
```
Returns all Texas cities classified in a specific climate region.

**Regions:** `desert`, `arctic`, `tropic`, `temperate`

**Example:** `GET /api/climate/region/temperate`

## Climate Features Extracted

For each city, the system extracts:

- **temperature** - Current temperature (°C)
- **apparent_temperature** - Feels-like temperature (°C)
- **humidity** - Relative humidity (%)
- **precipitation** - Current precipitation (mm)
- **weather_code** - WMO weather code
- **weather_description** - Human-readable weather description
- **wind_speed** - Wind speed at 10m height (m/s)
- **wind_direction** - Wind direction (degrees 0-360)
- **cloud_cover** - Cloud coverage (%)
- **elevation** - Site elevation (meters)
- **coordinates** - Latitude and longitude
- **timezone** - Timezone (IANA format)
- **timestamp** - Data collection timestamp (ISO 8601)

## Usage Examples

### Python Script Example

```python
from backend.climate import get_climate_analyzer

# Get analyzer instance
analyzer = get_climate_analyzer()

# Fetch and analyze all Texas cities
texas_data = analyzer.fetch_and_analyze_texas()

# Get cities in a specific region
tropic_cities = analyzer.get_region_cities('tropic')
print(f"Tropical cities: {tropic_cities}")

# Get detailed info for a city
austin = analyzer.get_city_details('Austin')
print(f"Austin region: {austin['region']}")
print(f"Austin temperature: {austin['features']['temperature']}°C")
```

### cURL Examples

```bash
# Get all Texas weather
curl http://localhost:5000/api/weather/texas

# Get regional distribution
curl http://localhost:5000/api/weather/regions

# Get Austin weather
curl http://localhost:5000/api/weather/city/Austin

# Get all temperate cities
curl http://localhost:5000/api/climate/region/temperate
```

## Customization

### Adding More Cities

Edit `backend/weather_service.py` - `TEXAS_CITIES` dictionary:

```python
TEXAS_CITIES = {
    'Houston': {'lat': 29.7604, 'lon': -95.3698},
    'Dallas': {'lat': 32.7767, 'lon': -96.7970},
    'YourCity': {'lat': YOUR_LAT, 'lon': YOUR_LON},  # Add here
    ...
}
```

### Adjusting Climate Thresholds

Edit `backend/weather_service.py` - `CLIMATE_THRESHOLDS` dictionary:

```python
CLIMATE_THRESHOLDS = {
    'desert': {
        'temp_min': 20,           # Minimum temperature (°C)
        'humidity_max': 40,       # Maximum humidity (%)
        'precipitation_max': 2.0  # Maximum precipitation (mm)
        ...
    },
    ...
}
```

### Using Fahrenheit

Open-Meteo returns Celsius by default. To convert to Fahrenheit:

```python
# In extract_climate_features method
'temperature': (current.get('temperature_2m', 0) * 9/5) + 32,
'apparent_temperature': (current.get('apparent_temperature', 0) * 9/5) + 32,
```

## Troubleshooting

### "Could not find coordinates for city"
- Verify the city name is spelled correctly
- Try using the city's full English name
- Check internet connection for geocoding API

### "Query execution failed"
- Check your internet connection
- Verify the city is in the supported list
- Test with a single city first

### No cities returned
- Verify city names are spelled correctly
- Ensure Open-Meteo API is accessible (check: https://api.open-meteo.com/)
- Try with a single city first

### Slow responses
- Open-Meteo has built-in rate limiting protection
- The system adds 0.5s delay between requests
- First run may take 3-5 seconds for all 5 cities

## Integration with Database

To store weather data in Snowflake:

```python
from backend.db import SnowflakeDB
from backend.climate import get_climate_analyzer

db = SnowflakeDB()
analyzer = get_climate_analyzer()

# Get data
texas_data = analyzer.fetch_and_analyze_texas()

# Insert into database (example)
for city, data in texas_data['cities'].items():
    region = data['region']
    features = data['features']
    # Execute insert query
    query = f"""
    INSERT INTO weather_data 
    (city, region, temperature, humidity, precipitation, wind_speed, timestamp)
    VALUES (
        '{city}', 
        '{region}', 
        {features['temperature']}, 
        {features['humidity']},
        {features['precipitation']},
        {features['wind_speed']},
        '{features['timestamp']}'
    )
    """
    db.execute_query(query)
```

## Future Enhancements

- [ ] Historical data storage and analysis
- [ ] Weather alerts for extreme conditions
- [ ] Predictive climate modeling
- [ ] Multi-country support
- [ ] Real-time dashboard
- [ ] Machine learning classification refinement

## License

See LICENSE file for details.
