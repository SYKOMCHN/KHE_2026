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

# ---------------- SIDEBAR ----------------
st.sidebar.title("Controls")

selected_biome = st.sidebar.selectbox(
    "Choose Biome",
    sorted(df["biome"].unique())
)

# Filter + SORT (VERY IMPORTANT FOR CHARTS)
filtered_df = df[df["biome"] == selected_biome].sort_values("year")

# ---------------- METRICS ----------------
st.subheader("Current Climate Stats")

latest = filtered_df.iloc[-1]

col1, col2, col3, col4 = st.columns(4)

col1.metric("🌡️ Temp (°C)", latest["metrics.avg_max_temp_c"])
col2.metric("🌧️ Precip (mm)", latest["metrics.total_precipitation_mm"])
col3.metric("💧 Humidity (%)", latest["metrics.avg_relative_humidity_pct"])
col4.metric("🌪️ Severe Days", latest["metrics.severe_weather_days"])

# ---------------- CHARTS ----------------
st.subheader("Climate Trends")

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Temperature Over Time**")
    st.line_chart(
        filtered_df.set_index("year")[["metrics.avg_max_temp_c"]]
    )

with col2:
    st.markdown("**Precipitation Over Time**")
    st.line_chart(
        filtered_df.set_index("year")[["metrics.total_precipitation_mm"]]
    )

# Optional extra (looks impressive)
st.subheader("Humidity Trend")
st.area_chart(
    filtered_df.set_index("year")[["metrics.avg_relative_humidity_pct"]]
)

# ---------------- FULL DATA ----------------
st.subheader("Full Climate Data (1979–2024)")

st.dataframe(
    filtered_df,
    use_container_width=True,
    height=400  # enables scrolling
)

# ---------------- INSIGHTS ----------------
st.subheader("Insights")

avg_temp = filtered_df["metrics.avg_max_temp_c"].mean()
avg_precip = filtered_df["metrics.total_precipitation_mm"].mean()

st.write(f"Average Temperature: {round(avg_temp, 2)} °C")
st.write(f"Average Precipitation: {round(avg_precip, 2)} mm")

if avg_temp > 30:
    st.error("🔥 High temperatures → harder survival")

elif avg_temp < 0:
    st.warning("❄️ Extreme cold → exposure risk")

if avg_precip < 200:
    st.warning("💧 Low rainfall → food scarcity risk")

else:
    st.success("✅ Conditions are relatively stable for survival")