import random

def calculate_year_stats(weather_data, current_pop):
    m = weather_data["metrics"]
    
    # S_famine: Low soil moisture + Low precipitation
    s_famine = (max(0, (0.2 - m.get('avg_soil_moisture_m3', 0.2)) * 2) + max(0, (300 - m.get('total_precipitation_mm', 300)) / 1000)) * 0.2
    
    # S_exposure: Days below freezing amplified by wind chill
    s_exposure = ((m.get('days_below_freezing', 0) / 365) * (1.0 + (m.get('avg_wind_speed_kmh', 0) / 100))) * 0.2
    
    # S_heatstroke: "Wet-bulb" effect.
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
    
    # Luck Factor (+/- 15% variance)
    luck_factor = random.uniform(0.85, 1.15)
    actual_surv = min(0.99, p_surv * luck_factor) 
    
    # Births and Deaths
    MAX_BIRTH_RATE = 0.15 
    births = int(current_pop * (MAX_BIRTH_RATE * actual_surv) * random.uniform(0.9, 1.1))
    deaths = int(current_pop * (1.0 - actual_surv) * random.uniform(0.9, 1.1))
    
    return births, deaths, actual_surv