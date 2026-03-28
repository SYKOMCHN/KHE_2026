import os
import requests
import statistics
import time
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# 1. MongoDB Connection Setup
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

# 2. Define Biome Coordinates
biomes = {
    "arctic": {"lat": 78.22, "lon": 15.65},       # Svalbard, Norway
    "tropic": {"lat": -3.11, "lon": -60.02},      # Manaus, Brazil (Amazon)
    "temperate": {"lat": 41.15, "lon": -81.36},   # Kent, Ohio
    "desert": {"lat": 23.41, "lon": 25.66}        # Sahara Desert, Egypt
}

# 3. The Fetch and Store Function
def fetch_and_store_climate(biome_name, lat, lon, year):
    print(f"Fetching {biome_name} data for {year}...")
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "auto"
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        weather_data = response.json()
        
        # Filter out missing data
        max_temps = [t for t in weather_data['daily']['temperature_2m_max'] if t is not None]
        precip = [p for p in weather_data['daily']['precipitation_sum'] if p is not None]
        
        if not max_temps:
            print(f"No temperature data found for {biome_name} in {year}.")
            return

        # Calculate metrics
        avg_max_temp = sum(max_temps) / len(max_temps)
        temp_deviation = statistics.stdev(max_temps) if len(max_temps) > 1 else 0
        total_precip = sum(precip)

        # Format the document for MongoDB
        yearly_document = {
            "biome": biome_name,
            "year": year,
            "metrics": {
                "avg_max_temp_c": round(avg_max_temp, 2),
                "temp_std_dev_c": round(temp_deviation, 2), # How much temp deviates
                "total_precipitation_mm": round(total_precip, 2),
                "days_below_freezing": len([t for t in max_temps if t < 0])
            }
        }

        # Insert into MongoDB
        climate_collection.insert_one(yearly_document)
        print(f"Success! Stored: {biome_name} {year} (Avg Temp: {round(avg_max_temp, 1)}°C, Deviation: ±{round(temp_deviation, 1)}°C)")
        
    else:
        print(f"Failed to fetch data for {biome_name}: HTTP {response.status_code}")

# 4. Run the data pipeline
# Example: Fetching data for the year 1979 for all 4 biomes
target_year = 1979

for name, coords in biomes.items():
    fetch_and_store_climate(name, coords["lat"], coords["lon"], target_year)
    # Be polite to the free API by pausing for 1 second between requests
    time.sleep(1)

print("Database population complete!")