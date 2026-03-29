import os
import requests
import statistics
import time
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# MongoDB connection
load_dotenv()
uri = os.getenv("MONGO_URI")
client = MongoClient(uri, server_api=ServerApi('1'))

# Define your database and collection
db = client["climate_db"]
climate_collection = db["climate_history"]

try:
    client.admin.command('ping')
    print("Successfully connected to MongoDB Atlas!")
except Exception as e:
    print(f"Connection error: {e}")

# biome coordinates
biomes = {
    "arctic": {"lat": 78.22, "lon": 15.65},       # Svalbard, Norway
    "tropic": {"lat": -3.11, "lon": -60.02},      # Manaus, Brazil (Amazon)
    "temperate": {"lat": 41.15, "lon": -81.36},   # Kent, Ohio
    "desert": {"lat": 23.41, "lon": 25.66}        # Sahara Desert, Egypt
}


# fetch and store the climate data
def fetch_and_store_climate(biome_name, lat, lon, year):
    print(f"Fetching {biome_name} data for {year}...")
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum", "wind_speed_10m_max", "weather_code"],
        "hourly": ["relative_humidity_2m", "soil_moisture_0_to_7cm"],
        "timezone": "auto"
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        weather_data = response.json()
        
        max_temps = [t for t in weather_data['daily']['temperature_2m_max'] if t is not None]
        precip = [p for p in weather_data['daily']['precipitation_sum'] if p is not None]
        wind_speeds = [w for w in weather_data['daily']['wind_speed_10m_max'] if w is not None]
        weather_codes = [c for c in weather_data['daily']['weather_code'] if c is not None]
        
        if not max_temps:
            print(f"No temperature data found for {biome_name} in {year}.")
            return

        # daily calculations
        avg_max_temp = sum(max_temps) / len(max_temps)
        temp_deviation = statistics.stdev(max_temps) if len(max_temps) > 1 else 0
        total_precip = sum(precip)
        avg_wind_speed = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0
        
        # WMO Weather Codes: Anything over 50 is generally severe (Heavy rain, snow, thunderstorms)
        severe_weather_days = len([c for c in weather_codes if c >= 51])

        # process hourly data
        humidity_data = [h for h in weather_data['hourly']['relative_humidity_2m'] if h is not None]
        moisture_data = [m for m in weather_data['hourly']['soil_moisture_0_to_7cm'] if m is not None]
        
        # convert soil moisture to cubic meters and want total volume for year
        avg_humidity = sum(humidity_data) / len(humidity_data) if humidity_data else 0
        avg_soil_moisture = sum(moisture_data) / len(moisture_data) if moisture_data else 0

        # format for DB
        yearly_document = {
            "biome": biome_name,
            "year": year,
            "metrics": {
                # Original Metrics
                "avg_max_temp_c": round(avg_max_temp, 2),
                "temp_std_dev_c": round(temp_deviation, 2), 
                "total_precipitation_mm": round(total_precip, 2),
                "days_below_freezing": len([t for t in max_temps if t < 0]),
                
                # New Metrics
                "avg_wind_speed_kmh": round(avg_wind_speed, 2),
                "avg_relative_humidity_pct": round(avg_humidity, 2),
                "avg_soil_moisture_m3": round(avg_soil_moisture, 3), # Measured in cubic meters
                "severe_weather_days": severe_weather_days
            }
        }

        # Insert into MongoDB
        climate_collection.insert_one(yearly_document)
        print(f"Success! Stored: {biome_name} {year}")
        
    else:
        print(f"Failed to fetch data for {biome_name}: HTTP {response.status_code}")

# run data pipeline for all biomes and years
print("Starting database population...")
for target_year in range(1979, 2025):
    for name, coords in biomes.items():
        fetch_and_store_climate(name, coords["lat"], coords["lon"], target_year)
        # request every
        time.sleep(1)

print("Database population complete!")