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

