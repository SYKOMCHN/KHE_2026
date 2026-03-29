import streamlit as st
import pandas as pd
import os
import pydeck as pdk
from PIL import Image
from pymongo import MongoClient
from dotenv import load_dotenv
from streamlit_image_coordinates import streamlit_image_coordinates

# ---------------- HELPER FUNCTIONS ----------------
def _squared_color_distance(c1, c2):
    return (c1[0] - c2[0]) ** 2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) ** 2


def find_best_biome(clicked_color, biome_palettes, tolerance=30):
    best_biome = None
    best_dist = float("inf")

    for biome, colors in biome_palettes.items(): 
        for palette_color in colors:
            dist = _squared_color_distance(clicked_color, palette_color)
            if dist < best_dist:
                best_dist = dist
                best_biome = biome

    if best_dist <= tolerance ** 2:
        return best_biome, best_dist
    return None, best_dist


# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="F.C.C.P.T. Simulator", layout="wide")

st.markdown("""
    <style>
    @import url("https://fonts.googleapis.com/css2?family=Patrick+Hand&display=swap");

    * {
        font-family: 'Patrick Hand', cursive,'Roboto', 'monospace';
    }
    </style>
""", unsafe_allow_html=True)

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
    st.title("Future Climate Conditions on Prehistoric Tribe Simulator")
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
            x_display = click_coords['x']
            y_display = click_coords['y']

            try:
                img = Image.open("assets/world_of_oog/world_of_oog.png").convert("RGB")
                orig_w, orig_h = img.size

                # streamlit_image_coordinates returns the rendered display size alongside
                # the click coordinates — use these to scale back to original pixel space
                display_w = click_coords.get('width', orig_w)
                display_h = click_coords.get('height', orig_h)

                # Scale display coords → original image coords
                x = int(x_display * orig_w / display_w)
                y = int(y_display * orig_h / display_h)

                r, g, b = img.getpixel((x, y))
                clicked_color = (r, g, b)

                # --- DEBUG EXPANDER (remove once colors are calibrated) ---
                #with st.expander("🎨 Debug: pixel info"):
                #    st.write(f"Display click: ({x_display}, {y_display})  →  Original pixel: ({x}, {y})")
                #    st.write(f"Color sampled: RGB{clicked_color}")

                # --- BIOME COLOR PALETTES ---
                # Use the debug expander above to click each biome and paste the
                # exact RGB values printed here.
                biome_palettes = {
                    "arctic":    [(152, 156, 175), (122, 126, 145)],
                    "temperate": [(115, 168, 108), (90, 140, 85)],
                    "desert":    [(201, 186, 99),  (180, 160, 80)],
                    "tropic":    [(189, 129, 99),  (160, 100, 80)],
                }

                # --- ROUTER: use find_best_biome for tolerance-based matching ---
                # This handles anti-aliased / edge pixels gracefully instead of
                # requiring an exact color hit.
                matched_biome, dist = find_best_biome(clicked_color, biome_palettes, tolerance=30)

                if matched_biome:
                    st.session_state.current_view = matched_biome
                else:
                    st.toast("🌊 You clicked the ocean or a border! Please click a landmass.", icon="⚠️")

                # Reroute if a valid biome was matched
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


    # --- FILTER DATA FOR THIS BIOME ---
    biome = st.session_state.current_view
    biome_df = df[df["biome"] == biome]

    # --- PER-BIOME CONTENT ---
    if biome == "arctic":
        zoom_artic = Image.open("assets/zoom_image/arctic_zoom.png").convert("RGB")
        
        st.image(zoom_artic, caption='Arctic Biome', use_column_width=True)
        
    elif biome == "temperate":
        zoom_temperate = Image.open("assets/zoom_image/temperate_zoom.png").convert("RGB")
        st.image(zoom_temperate, caption='Temperate Biome', use_column_width=True)
    elif biome == "desert":
        zoom_desert = Image.open("assets/zoom_image/desert_zoom.png").convert("RGB")
        st.image(zoom_desert, caption='Desert Biome', use_column_width=True)
    elif biome == "tropic":
        zoom_tropic = Image.open("assets/zoom_image/tropic_zoom.png").convert("RGB")
        st.image(zoom_tropic, caption='Tropic Biome', use_column_width=True)

   # st.info(f"You have successfully navigated to the {st.session_state.current_view.upper()} simulation environment.")