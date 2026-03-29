import os
import time
import random # Added for real-life probability variance
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

# db connection
load_dotenv()
uri = os.getenv("MONGO_URI")
client = MongoClient(uri, server_api=ServerApi('1'))

db = client["climate_db"]
climate_collection = db["climate_history"]
analytics_collection = db["simulation_results"]

# core math for birth/death based on stressors
def calculate_year_stats(weather_data, current_pop):
    m = weather_data["metrics"]
    
    # S_famine: Low soil moisture + Low precipitation (drought)
    # Soil moisture is usually 0.1 to 0.4. Below 0.2 triggers famine.
    # Scaled down by 0.2 so it causes hardship, not instant extinction
    s_famine = (max(0, (0.2 - m.get('avg_soil_moisture_m3', 0.2)) * 2) + max(0, (300 - m.get('total_precipitation_mm', 300)) / 1000)) * 0.2
    
    # S_exposure: Days below freezing amplified by wind chill
    s_exposure = ((m.get('days_below_freezing', 0) / 365) * (1.0 + (m.get('avg_wind_speed_kmh', 0) / 100))) * 0.2
    
    # S_heatstroke: "Wet-bulb" effect. Temps over 25C combined with humidity.
    s_heatstroke = 0
    if m.get('avg_max_temp_c', 0) > 25:
        s_heatstroke = (((m['avg_max_temp_c'] - 25) * (m.get('avg_relative_humidity_pct', 50) / 100)) * 0.05) * 0.2
        
    # S_chaos: Unpredictable weather prevents preparation
    s_chaos = (m.get('temp_std_dev_c', 0) * 0.015) * 0.2
    
    # S_severe_weather: Direct fatalities from storms/floods
    s_severe = ((m.get('severe_weather_days', 0) / 365) * 0.5) * 0.2

    # Calculate final Survival Probability
    total_stress = s_famine + s_exposure + s_heatstroke + s_chaos + s_severe
    p_surv = max(0.01, 1.0 - total_stress) 
    
    # --- ADDING TRUE PROBABILITY / RANDOMNESS ---
    # Apply a "Luck Factor" (+/- 15% variance) so every run is unique
    luck_factor = random.uniform(0.85, 1.15)
    actual_surv = min(0.99, p_surv * luck_factor) # Cap max survival at 99%
    
    # Calculate Births and Deaths
    MAX_BIRTH_RATE = 0.15 # 15% biological maximum
    
    # Add minor random noise to the exact headcounts to prevent identical numbers
    births = int(current_pop * (MAX_BIRTH_RATE * actual_surv) * random.uniform(0.9, 1.1))
    deaths = int(current_pop * (1.0 - actual_surv) * random.uniform(0.9, 1.1))
    
    return births, deaths, actual_surv

# sim loop
def run_interactive_sim():
    # Automatically clear the database on startup so you don't have to go back
    print("Clearing old simulation data from MongoDB...")
    analytics_collection.delete_many({})
    
    print("\nFUTURISTIC CAVEMEN SIM!!!!!!!!")
    print("Type 'stop' at any prompt to exit.\n")
    
    # lock in biome
    while True:
        biome_input = input("Enter biome to simulate (arctic, tropic, temperate, desert): ").lower().strip()
        if biome_input == 'stop': return
        
        # Fetch ALL weather data for this biome upfront (usually ~47 records)
        # We do this here so we can infinitely loop through the weather later
        all_weather = list(climate_collection.find({"biome": biome_input}).sort("year", 1))
        
        if not all_weather:
            print("No data found for that biome. Check spelling and try again.\n")
            continue
            
        break # Valid biome found, exit this first loop
        
    print(f"\n{biome_input.upper()} Environment")

    # loop for amount of years
    while True:
        years_input = input(f"Years to simulate? (limit to 1000, or 'stop' to exit): ")
        if years_input == 'stop': break
        
        try:
            num_years = int(years_input)
        except ValueError:
            print("Please enter a valid number.\n")
            continue

        # State Retrieval Logic: Find where we left off
        last_run = analytics_collection.find_one(
            {"biome": biome_input},
            sort=[("simulation_year", -1)]
        )
        
        if last_run:
            current_population = last_run["population"]
            current_sim_year = last_run["simulation_year"]
            sim_id = last_run["simulation_id"]
            
            print(f"\nResuming {biome_input.upper()} simulation from Year {current_sim_year}...")
            print(f"Starting Population: {current_population}")
            print("-" * 60)
        else:
            current_population = 10000 #starting population
            current_sim_year = 0
            sim_id = f"sim_{int(time.time())}"
            
            print(f"\nDropping {current_population} cavemen into the {biome_input.upper()}...")
            print("-" * 60)
            
            # Inject 1978 Baseline (Year 0)
            baseline_record = {
                "simulation_id": sim_id,
                "biome": biome_input,
                "historical_year_used": 1978,
                "simulation_year": current_sim_year,
                "population": current_population,
                "births": 0,
                "deaths": 0,
                "survival_probability": 1.0
            }
            analytics_collection.insert_one(baseline_record)
            print(f"Year 0 (Baseline 1978) | Pop: {current_population} | Births: 0 | Deaths: 0 | Survival Chance: 100.0%")
            time.sleep(0.2)

        # run the actual sim
        for _ in range(num_years):
            if current_population <= 0:
                print(f"EXTINCTION. The population did not survive past year {current_sim_year}.")
                break
                
            # Infinite Weather Loop: Maps the current sim year to an index in your dataset
            weather_idx = current_sim_year % len(all_weather)
            weather_year = all_weather[weather_idx]
            actual_year = weather_year["year"]
            
            current_sim_year += 1 # Advance the permanent timeline
            
            # Run Math
            births, deaths, p_surv = calculate_year_stats(weather_year, current_population)
            
            # Update Population
            current_population = current_population + births - deaths
            if current_population < 0: current_population = 0
            
            # Save to Database
            sim_record = {
                "simulation_id": sim_id,
                "biome": biome_input,
                "historical_year_used": actual_year,
                "simulation_year": current_sim_year,
                "population": current_population,
                "births": births,
                "deaths": deaths,
                "survival_probability": round(p_surv, 3)
            }
            analytics_collection.insert_one(sim_record)
            
            # Print to console
            print(f"Year {current_sim_year} (Using {actual_year}) | Pop: {current_population} | Births: {births} | Deaths: {deaths} | Survival Chance: {round(p_surv*100,1)}%")
            time.sleep(0.1) 
            
        print("-" * 60)
        print(f"Simulation Paused. Current Population: {current_population}")
        print("Results saved to 'simulation_results' collection.\n")

if __name__ == "__main__":
    run_interactive_sim()