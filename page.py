import streamlit as st
import pandas as pd
import os
from pymongo import MongoClient
from dotenv import load_dotenv

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Futuristic Tribe Simulator", layout="wide")

st.title("Futuristic Tribe Simulator")

# ---------------- LOAD ENV ----------------
load_dotenv()

# ---------------- DB CONNECTION ----------------
@st.cache_resource
def get_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    return client["climate_db"]

db = get_db()
collection = db["climate_history"]

# ---------------- LOAD DATA ----------------
@st.cache_data
def load_climate_data():
    data = list(collection.find({}, {"_id": 0}))
    df = pd.json_normalize(data)
    return df

df = load_climate_data()

# ---------------- SIDEBAR ------NOT ANY MORE!!!!!!!!!!!
# st.sidebar.title("Controls")

# selected_biome = st.sidebar.selectbox(
#     "Choose Biome",
#     sorted(df["biome"].unique())
# )

# Filter + SORT (VERY IMPORTANT FOR CHARTS)
# filtered_df = df[df["biome"] == selected_biome].sort_values("year")

# ---------------- METRICS ----------------
st.subheader("Climate Averages (1979–2024)")

# Calculate averages across the entire dataset (all biomes, all years)
global_avg_temp = df["metrics.avg_max_temp_c"].mean()
global_avg_precip = df["metrics.total_precipitation_mm"].mean()
global_avg_humidity = df["metrics.avg_relative_humidity_pct"].mean()
global_avg_severe = df["metrics.severe_weather_days"].mean()


col1, col2, col3, col4 = st.columns(4)

col1.metric("Temp (°C)", round(global_avg_temp, 2))
col2.metric("Precip (mm)", round(global_avg_precip, 2))
col3.metric("Humidity (%)", round(global_avg_humidity, 2))
col4.metric("Avg Severe Days/Yr", round(global_avg_severe, 1))

# ---------------- CHARTS ----------------
st.subheader("Climate Trends")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Temperature Over Time (°C)**")
    # Pivot: Index = X-axis, Columns = the 4 lines, Values = Y-axis data
    temp_pivot = df.pivot(index="year", columns="biome", values="metrics.avg_max_temp_c")
    st.line_chart(temp_pivot)

with col2:
    st.markdown("**Precipitation Over Time (mm)**")
    precip_pivot = df.pivot(index="year", columns="biome", values="metrics.total_precipitation_mm")
    st.line_chart(precip_pivot)

# Optional extra (looks impressive)
st.subheader("Humidity Trend (%)")
# Pivot: Index = X-axis, Columns = the 4 lines, Values = Y-axis data
humidity_pivot = df.pivot(index="year", columns="biome", values="metrics.avg_relative_humidity_pct")
st.area_chart(humidity_pivot)

# ---------------- FULL DATA ----------------
st.subheader("Full Climate Data (1979–2024)")
# Sort by year, then biome, so it reads chronologically and cleanly

full_sorted_df = df.sort_values(by=["year", "biome"]).reset_index(drop=True)

st.dataframe( #rename to readable format
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
    height=400  # enables scrolling
)

# ---------------- INSIGHTS ----------------
st.subheader("Overall Insights")

st.write(f"Average Overall Temperature: **{round(global_avg_temp, 2)} °C**")
st.write(f"Average Overall Precipitation: **{round(global_avg_precip, 2)} mm**")

if global_avg_temp > 30:
    st.error("Baseline temperatures are highly volatile → harder survival.")
elif global_avg_temp < 0:
    st.warning("Baseline is freezing → extreme exposure risk.")
else:
    st.info("Temperatures sit in a moderate baseline, though specific biomes vary wildly.")

if global_avg_precip < 200:
    st.warning("GBaseline indicates severe drought → food scarcity risk.")
else:
    st.success("Precipitation baseline is sufficient to sustain primitive agriculture.")