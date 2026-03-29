import streamlit as st
import pandas as pd
import os
from pymongo import MongoClient
from dotenv import load_dotenv

st.set_page_config(page_title="Futuristic Tribe Simulator", layout="wide")

st.title("Futuristic Tribe Simulator")

# Load environment variables from .env file
load_dotenv()

# Connect to MongoDB and get the database and collection from the climate api
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

biome = st.selectbox(" Select Biome", df["biome"].unique())

filtered_df = df[df["biome"] == biome]

st.subheader("📊 Current Climate Stats")

latest = filtered_df.sort_values("year").iloc[-1]

col1, col2, col3, col4 = st.columns(4)

col1.metric("🌡️ Temp (°C)", latest["metrics.avg_max_temp_c"])
col2.metric("🌧️ Precip (mm)", latest["metrics.total_precipitation_mm"])
col3.metric("💧 Humidity (%)", latest["metrics.avg_relative_humidity_pct"])
col4.metric("🌪️ Severe Days", latest["metrics.severe_weather_days"])

st.subheader("📈 Climate Trends")

col1, col2 = st.columns(2)

with col1:
    st.line_chart(
        filtered_df.set_index("year")["metrics.avg_max_temp_c"]
    )

with col2:
    st.line_chart(
        filtered_df.set_index("year")["metrics.total_precipitation_mm"]
    )

    st.subheader("📋 Full Data")

st.dataframe(filtered_df.tail(10))


st.subheader("🧠 Insights")

avg_temp = filtered_df["metrics.avg_max_temp_c"].mean()
avg_precip = filtered_df["metrics.total_precipitation_mm"].mean()

if avg_temp > 30:
    st.error("🔥 High temperatures → harder survival")

if avg_precip < 200:
    st.warning("💧 Low rainfall → food scarcity risk")

st.success("✅ Moderate conditions improve survival chances")

st.sidebar.title("🪨 Controls")

selected_biome = st.sidebar.selectbox(
    "Choose Biome",
    df["biome"].unique()
)

filtered_df = df[df["biome"] == selected_biome]

