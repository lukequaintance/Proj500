import os
import sys

# Check if the app has already been launched via Streamlit
if not os.environ.get("STREAMLIT_STARTED"):
    os.environ["STREAMLIT_STARTED"] = "1"
    os.system("python -m streamlit run app.py")
    sys.exit()  # Exit to prevent running the rest of the code in this process

import json
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Set page config
st.set_page_config(page_title="Field Data Visualization", layout="wide")

st.title("Field Data Visualization Application")

st.markdown("""
This application allows you to upload a JSON file that contains two sets of data:
- **Sensor Data:** Includes sensor readings (NPK, pH, temperature, moisture) along with GPS coordinates.
- **Plant Data:** Contains plant image classification results (with a flag for harmful plants) along with GPS coordinates.

The app will display:
- A map showing markers for harmful plants.
- A heatmap of sensor readings (in this example, the NPK value is visualized).
""")

st.sidebar.header("Data Upload")
uploaded_file = st.sidebar.file_uploader("Upload your JSON file", type=["json"])

if uploaded_file is not None:
    try:
        # Read the uploaded JSON file
        data = json.load(uploaded_file)
        sensor_data = data.get("sensor_data", [])
        plant_data = data.get("plant_data", [])

        st.success("File successfully loaded!")

        # --- Create Map for Harmful Plants ---
        st.subheader("Map: Harmful Plants")
        # Choose a default center (could be the mean of the coordinates)
        if plant_data:
            avg_lat = sum(item["latitude"] for item in plant_data) / len(plant_data)
            avg_lon = sum(item["longitude"] for item in plant_data) / len(plant_data)
        else:
            avg_lat, avg_lon = 0, 0

        plant_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)

        for plant in plant_data:
            lat = plant.get("latitude")
            lon = plant.get("longitude")
            name = plant.get("species", "Unknown")
            harmful = plant.get("plant_status", "").lower() == "harmful"  # Normalize case

            Simple_name = plant.get("custom_classification")
            filename = plant.get ("filename")

            # Only add marker if the plant is flagged as harmful
            if harmful:
                popup_text = f"{name}, also known as {Simple_name} <br> view the image {filename} <br> (Harmful)"
                # Create a Popup with a custom max_width (in pixels)
                popup = folium.Popup(popup_text, max_width=300)
                folium.Marker(
                    location=[lat, lon],
                    popup=popup,
                    icon=folium.Icon(color="red", icon="exclamation-triangle", prefix='fa')
                ).add_to(plant_map)

        st_data = st_folium(plant_map, width=700, height=500)

        # --- Create Heatmap for Sensor Data ---
        st.subheader("Map: Sensor Data Heatmap (NPK values)")
        if sensor_data:
            # Use sensor data coordinates and the sensor value for the heat intensity.
            # You can change "npk" to "ph", "temperature", etc. as needed.
            heat_data = []
            for sensor in sensor_data:
                lat = sensor.get("latitude")
                lon = sensor.get("longitude")
                npk = sensor.get("npk", 0)
                # HeatMap expects points as [lat, lon, intensity]
                heat_data.append([lat, lon, npk])

            # Use an average location from sensor data for map center:
            avg_lat = sum(item["latitude"] for item in sensor_data) / len(sensor_data)
            avg_lon = sum(item["longitude"] for item in sensor_data) / len(sensor_data)

            sensor_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)
            # Create heatmap layer. Adjust parameters (radius, blur, min_opacity) as needed.
            HeatMap(heat_data, radius=15, blur=10, min_opacity=0.2, max_zoom=18).add_to(sensor_map)
            st_data2 = st_folium(sensor_map, width=700, height=500)
        else:
            st.warning("No sensor data found in the uploaded file.")

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
else:
    st.info("Awaiting JSON file upload. (See sidebar)")
