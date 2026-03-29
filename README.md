# KHE_2026

## Project Overview: Futuristic Tribe Simulator
This is a population dynamics simulation based on real-world climate data. It drops virtual tribes into different biomes and simulates their survival based on environmental stressors derived from historical weather data.

### Architecture & Technology Stack
Frontend (Web UI)
Streamlit - Interactive web framework for the user interface
Plotly Express - Interactive data visualizations (charts, heatmaps)
Pandas - Data manipulation and analysis
PIL (Pillow) - Image processing
streamlit-image-coordinates - Click detection on map images

### Backend & Data
MongoDB - NoSQL database storing climate and simulation data
Python - Core application logic
Open-Meteo API - Historical weather data source (free, no API key needed)
Key Python Files

### How It Works
1. Data Pipeline: Climate History Generation
2. Simulation Core: Survival Probability Formula
The app calculates survival chance using 5 environmental stressors:

Each stressor is capped at 0.2 (20%) weight.

### 3. Population Dynamics
Two User Interfaces
#### Option 1: Web UI (page.py) - Currently Running
World View: Interactive map → click biome to enter simulation
Climate Analytics: Global trends (temperature, precipitation, humidity heatmap)
Biome Simulation:
Visual biome zoom
Real-time population chart
Control years to simulate
Live birth/death metrics

#### Option 2: CLI (simulator.py) - Terminal-based
Command-line version of the same simulation
No visual interface, just text output
Data Flow Diagram
MongoDB Collections
Climate History (climate_db.climate_history)
Simulation Results (climate_db.simulation_results)
