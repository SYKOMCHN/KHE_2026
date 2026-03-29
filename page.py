import streamlit as st
import pandas as pd
import os
from PIL import Image
from pymongo import MongoClient
from dotenv import load_dotenv
from streamlit_image_coordinates import streamlit_image_coordinates

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Futuristic Tribe Simulator", layout="wide")

# ---------------- LOAD ENV & DB ----------------
load_dotenv()

@st.cache_resource
def get_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    return client["climate_db"]

db = get_db()
collection = db["climate_history"]

@st.cache_data
def load_climate_data():
    data = list(collection.find({}, {"_id": 0}))
    df = pd.json_normalize(data)
    return df

df = load_climate_data()

# ---------------- SESSION STATE (ROUTER) ----------------
if "current_view" not in st.session_state:
    st.session_state.current_view = "world"

# =========================================================
#                     PAGE 1: WORLD VIEW
# =========================================================
if st.session_state.current_view == "world":
    st.title("Futuristic Tribe Simulator")
    st.subheader("Interactive World Map")
    
    spacer_left, map_col, spacer_right = st.columns([1, 2, 1])
    
    with map_col:
        st.markdown("<p style='text-align: center;'>Click a colored landmass to enter simulation.</p>", unsafe_allow_html=True)
        
        click_coords = streamlit_image_coordinates(
            "assets/world_of_oog/world_of_oog.png", 
            key="map",
            use_column_width=True
        )
        
        if click_coords is not None:
            x = click_coords['x']
            y = click_coords['y']
            
            try:
                img = Image.open("assets/world_of_oog/world_of_oog.png").convert("RGB")
                r, g, b = img.getpixel((x, y))
                clicked_color = (r, g, b)
                
                # --- CALIBRATION TOOL ---
                # Click the different shades on your map to get their exact RGB values
                st.warning(f"You clicked Pixel Color: {clicked_color}")
                
                # --- EXACT SHAPE HITBOX LOGIC (MULTI-COLOR) ---
                # Replace these placeholder tuples with the exact RGB values from your calibration tool!
                
                # Example: Put both shades of Arctic blue/grey here
                arctic_colors = [(152, 156, 175), (122, 126, 145)] 
                
                # Example: Put the shades of green here
                temperate_colors = [(115, 168, 108), (90, 140, 85)] 
                
                # Example: Put the shades of tan/yellow here
                desert_colors = [(201, 186, 99), (180, 160, 80)] 
                
                # Example: Put the shades of brown/orange here
                tropic_colors = [(189, 129, 99), (160, 100, 80)] 
                
                # --- THE ROUTER ---
                if clicked_color in arctic_colors:
                    st.session_state.current_view = "arctic"
                elif clicked_color in temperate_colors:
                    st.session_state.current_view = "temperate"
                elif clicked_color in desert_colors:
                    st.session_state.current_view = "desert"
                elif clicked_color in tropic_colors:
                    st.session_state.current_view = "tropic"
                else:
                    st.toast("🌊 You clicked a border or the ocean! Please click a landmass.", icon="⚠️")
                    
                # Reroute if a valid color was clicked
                if st.session_state.current_view != "world":
                    st.rerun() 
                    
            except Exception as e:
                st.error(f"Image processing error: {e}")

    st.divider()

    # --- GLOBAL METRICS ---
    st.subheader("Climate Averages (1979–2024)")

    global_avg_temp = df["metrics.avg_max_temp_c"].mean()
    global_avg_precip = df["metrics.total_precipitation_mm"].mean()
    global_avg_humidity = df["metrics.avg_relative_humidity_pct"].mean()
    global_avg_severe = df["metrics.severe_weather_days"].mean()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Temp (°C)", round(global_avg_temp, 2))
    col2.metric("Precip (mm)", round(global_avg_precip, 2))
    col3.metric("Humidity (%)", round(global_avg_humidity, 2))
    col4.metric("Avg Severe Days/Yr", round(global_avg_severe, 1))

    # --- CHARTS ---
    st.subheader("Climate Trends")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Temperature Over Time (°C)**")
        temp_pivot = df.pivot(index="year", columns="biome", values="metrics.avg_max_temp_c")
        st.line_chart(temp_pivot)

    with col2:
        st.markdown("**Precipitation Over Time (mm)**")
        precip_pivot = df.pivot(index="year", columns="biome", values="metrics.total_precipitation_mm")
        st.line_chart(precip_pivot)

    st.subheader("Humidity Trend (%)")
    humidity_pivot = df.pivot(index="year", columns="biome", values="metrics.avg_relative_humidity_pct")
    st.area_chart(humidity_pivot)

    # --- FULL DATA ---
    st.subheader("Full Climate Data (1979–2024)")
    full_sorted_df = df.sort_values(by=["year", "biome"]).reset_index(drop=True)

    st.dataframe( 
        full_sorted_df.rename(columns={
            "year": "Year",
            "biome": "Biome",
            "metrics.avg_max_temp_c": "Avg Max Temp (°C)",
            "metrics.temp_std_dev_c": "Temp Std Dev (°C)",
            "metrics.total_precipitation_mm": "Total Precip (mm)",
            "metrics.days_below_freezing": "Days < 0°C",
            "metrics.avg_wind_speed_kmh": "Avg Wind Speed (km/h)",
            "metrics.avg_relative_humidity_pct": "Avg Humidity (%)",
            "metrics.avg_soil_moisture_m3": "Avg Soil Moisture (m³)",
            "metrics.severe_weather_days": "Severe Weather Days"
        }),
        use_container_width=True,
        height=400 
    )

# =========================================================
#               PAGE 2: THE EMPTY BIOME CANVAS
# =========================================================
else:
    col1, col2 = st.columns([8, 2])
    with col1:
        st.title(f"Simulation: {st.session_state.current_view.upper()} REGION")
    with col2:
        st.write("") 
        if st.button("🔙 Return to World Map", use_container_width=True):
            st.session_state.current_view = "world"
            st.rerun()
            
    st.divider()

    st.info(f"You have successfully navigated to the {st.session_state.current_view.upper()} simulation environment.")