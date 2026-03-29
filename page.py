import streamlit as st
import plotly.express as px
import pandas as pd
import os
import time
from PIL import Image
from pymongo import MongoClient
from dotenv import load_dotenv
from streamlit_image_coordinates import streamlit_image_coordinates
import base64

# import simulate.py file
from simulate import calculate_year_stats

# ---------------- HELPER FUNCTIONS ----------------

def show_gif(path, width=180):
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    st.markdown(
        f'<img src="data:image/gif;base64,{data}" width="{width}">',
        unsafe_allow_html=True
    )

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
st.set_page_config(page_title="Futuristic Tribe Simulator", layout="wide")

st.markdown("""
    <style>
    @import url("https://fonts.googleapis.com/css2?family=Patrick+Hand&display=swap");
    * {
        font-family: 'Patrick Hand', cursive,'Roboto', 'monospace';
    }
    </style>
""", unsafe_allow_html=True)

# load env to get MongoDB URI
load_dotenv()

@st.cache_resource
def get_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    return client["climate_db"]

db = get_db()
collection = db["climate_history"]
analytics_collection = db["simulation_results"] 

@st.cache_data
def load_climate_data():
    data = list(collection.find({}, {"_id": 0}))
    df = pd.json_normalize(data)
    return df

df = load_climate_data()

# session state to track page
if "current_view" not in st.session_state:
    st.session_state.current_view = "world"

# =========================================================
#                     PAGE 1: WORLD VIEW
# =========================================================
if st.session_state.current_view == "world":

    # --- BEAUTIFUL UI SUMMARY BANNER ---
    st.markdown("""
    <div style="
        text-align: center;
        padding: 30px 20px;
        border-radius: 15px;
        background: linear-gradient(135deg, #1f2937, #374151);
        color: white;
        box-shadow: 0 8px 20px rgba(0,0,0,0.25);
        margin-bottom: 30px;
    ">
    <h1 style="margin-bottom: 10px;"> Futuristic Tribe Simulator</h1>
    <p style="font-size:18px; max-width:800px; margin:auto; line-height:1.6;">
    Explore how <b>climate conditions shape the survival of the caveman's population </b> over time.
    Using real-world data from <b>1979–2024</b>, this simulation allows you to analyze environmental trends and model population outcomes.
    </p>
    <br>
    <div style="display: flex; justify-content: center; gap: 40px; flex-wrap: wrap; margin-top: 15px;">
    <div>
     <b>Select a Region</b><br>
    <span style="font-size:14px;">Choose a region from the map</span>
    </div>
    <div>
     <b>Analyze Climate</b><br>
    <span style="font-size:14px;">View temperature, precipitation, and humidity trends</span>
    </div>           
    <div>
     <b>Run Simulations</b><br>
    <span style="font-size:14px;">Model population survival under environmental stress</span>
    </div>
    </div>
    <br>
    <p style="font-size:24px; margin-top:20px;">
     Click a colored landmass below to begin your simulation
    </p>
    </div>
    """, unsafe_allow_html=True)

    # Use columns to constrain the map size and add goofy cavemen
    spacer_left, map_col, spacer_right = st.columns([1, 2, 1])

    # Place caveman GIF on the left side 
    with spacer_left:
        st.write("") 
        st.write("")
        show_gif("assets/ooga_idle_gif.gif", width=256)

    # Place caveman GIF on the right side
    with spacer_right:
        st.write("") 
        st.write("")
        show_gif("assets/ooga_idle_gif.gif", width=256)

    with map_col:
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

                display_w = click_coords.get('width', orig_w)
                display_h = click_coords.get('height', orig_h)

                x = int(x_display * orig_w / display_w)
                y = int(y_display * orig_h / display_h)

                r, g, b = img.getpixel((x, y))
                clicked_color = (r, g, b)

                biome_palettes = {
                    "arctic":    [(152, 156, 175), (122, 126, 145)],
                    "temperate": [(115, 168, 108), (90, 140, 85)],
                    "desert":    [(201, 186, 99),  (180, 160, 80)],
                    "tropic":    [(189, 129, 99),  (160, 100, 80)],
                }

                matched_biome, dist = find_best_biome(clicked_color, biome_palettes, tolerance=30)

                if matched_biome:
                    # THIS IS THE FIX: Delete data BEFORE switching views
                    analytics_collection.delete_many({"biome": matched_biome})
                    st.session_state.current_view = matched_biome
                else:
                    st.toast("You clicked the ocean or a border! Please click a landmass.", icon="⚠️")

                if st.session_state.current_view != "world":
                    st.rerun()

            except Exception as e:
                st.error(f"Image processing error: {e}")

    st.divider()

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

    st.subheader("Humidity Heatmap (%)")
    st.caption("Drag to zoom into a specific time period")
    year_range = st.slider(
        "Select Year Range",
        int(df.year.min()),
        int(df.year.max()),
        (1979, 2024) 
    )

    filtered_df = df[
        (df["year"] >= year_range[0]) & 
        (df["year"] <= year_range[1])
    ]

    humidity_pivot = filtered_df.pivot(
        index="biome",
        columns="year",
        values="metrics.avg_relative_humidity_pct"
    )

    fig = px.imshow(
        humidity_pivot,
        aspect="auto",
        color_continuous_scale="YlGnBu",
        labels=dict(x="Year", y="Biome", color="Humidity (%)")
    )

    fig.update_layout(
        xaxis=dict(tickangle=45),
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

# =========================================================
#               PAGE 2: THE BIOME SIMULATION
# =========================================================
else:
    biome = st.session_state.current_view
    
    # back button
    col1, col2 = st.columns([8, 2])
    with col1:
        st.title(f"Simulation: {biome.upper()} REGION")
    with col2:
        st.write("") 
        
        if st.button("Return to World Map"):
            st.session_state.current_view = "world"
            st.rerun()

    st.divider()

    # split the screen into 2 columns
    map_col, sim_col = st.columns([1, 2]) 

    # left side: map and controls
    with map_col:
        try:
            zoom_img = Image.open(f"assets/zoom_image/{biome}_zoom.png").convert("RGB")
            st.image(zoom_img, caption=f'{biome.capitalize()} Biome', use_container_width=True)
        except Exception as e:
            st.warning(f"Could not load image: assets/zoom_image/{biome}_zoom.png")

        years_to_sim = st.number_input("Years to Simulate", min_value=1, max_value=500, value=10, step=10)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            start_sim = st.button("Simulate", use_container_width=True)
        with col_btn2:
            reset_sim = st.button("Reset", use_container_width=True)
            
        if reset_sim:
            analytics_collection.delete_many({"biome": biome})
            st.toast("Simulation data cleared.")
            st.rerun()

    # live dashboard on right
    with sim_col:
        st.markdown("### Population Dynamics")
        
        metrics_placeholder = st.empty()
        chart_placeholder = st.empty()

        all_weather = list(collection.find({"biome": biome}).sort("year", 1))
        last_run = analytics_collection.find_one({"biome": biome}, sort=[("simulation_year", -1)])
        
        if last_run:
            current_pop = last_run["population"]
            current_sim_year = last_run["simulation_year"]
            sim_id = last_run["simulation_id"]
        else:
            current_pop = 10000
            current_sim_year = 0
            sim_id = f"sim_{int(time.time())}"
            analytics_collection.insert_one({
                "simulation_id": sim_id, "biome": biome, "historical_year_used": 1978,
                "simulation_year": current_sim_year, "population": current_pop,
                "births": 0, "deaths": 0, "survival_probability": 1.0
            })

        history = list(analytics_collection.find({"biome": biome}).sort("simulation_year", 1))
        chart_data = [{"Year": h["simulation_year"], "Population": h["population"]} for h in history]

        if chart_data:
            df_chart = pd.DataFrame(chart_data).set_index("Year")
            chart_placeholder.line_chart(df_chart, color="#2ecc71") 
            
            with metrics_placeholder.container():
                m1, m2, m3 = st.columns(3)
                m1.metric("Current Population", f"{current_pop:,}")
                m2.metric("Latest Births", history[-1]["births"])
                m3.metric("Latest Deaths", f'-{history[-1]["deaths"]}')

        # --- THE REAL-TIME SIMULATION LOOP ---
        if start_sim and all_weather:
            for _ in range(years_to_sim):
                if current_pop <= 0:
                    st.error("Extinction Reached.")
                    break
                
                weather_idx = current_sim_year % len(all_weather)
                weather_year = all_weather[weather_idx]
                
                current_sim_year += 1
                
                births, deaths, p_surv = calculate_year_stats(weather_year, current_pop)
                
                current_pop = current_pop + births - deaths
                if current_pop < 0: current_pop = 0
                
                analytics_collection.insert_one({
                    "simulation_id": sim_id, "biome": biome, "historical_year_used": weather_year["year"],
                    "simulation_year": current_sim_year, "population": current_pop,
                    "births": births, "deaths": deaths, "survival_probability": round(p_surv, 3)
                })
                
                chart_data.append({"Year": current_sim_year, "Population": current_pop})
                df_chart = pd.DataFrame(chart_data).set_index("Year")
                
                chart_placeholder.line_chart(df_chart, color="#2ecc71") 
                
                with metrics_placeholder.container():
                    m1, m2, m3 = st.columns(3)
                    m1.metric("Current Population", f"{current_pop:,}", delta=births-deaths)
                    m2.metric("Latest Births", births)
                    m3.metric("Latest Deaths", f"-{deaths}") 
                
                time.sleep(0.5)

    # math footer
    st.divider()
    st.subheader("Simulation Mathematics")
    st.markdown("Survival probability ($P_{surv}$) is calculated by deriving environmental stressors from real-world Open-Meteo data:")
    st.latex(r"P_{surv} = \max(0.01, 1.0 - (S_{famine} + S_{exposure} + S_{heatstroke} + S_{chaos} + S_{severe\_weather}))")
    
    st.markdown("")
    
    col_math1, col_math2, col_math3 = st.columns(3)
    with col_math1:
        st.markdown("<p style='text-align: center;'><b>Birth Formula</b></p>", unsafe_allow_html=True)
        st.latex(r"Births = P_{current} \times (R_{max} \times P_{surv})")
    with col_math2:
        st.markdown("<p style='text-align: center;'><b>Death Formula</b></p>", unsafe_allow_html=True)
        st.latex(r"Deaths = P_{current} \times (1 - P_{surv})")
    with col_math3:
        st.markdown("<p style='text-align: center;'><b>New Population Formula</b></p>", unsafe_allow_html=True)
        st.latex(r"P_{new} = P_{current} + Births - Deaths")