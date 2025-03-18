import os
import sys
import json
import base64
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Check if the app has already been launched via Streamlit
if not os.environ.get("STREAMLIT_STARTED"):
    os.environ["STREAMLIT_STARTED"] = "1"
    os.system("python -m streamlit run app.py")
    sys.exit()

# Set page config
st.set_page_config(page_title="Field Data Visualization", layout="wide")

st.title("Field Data Visualization Application")

st.sidebar.header("Data Upload")
uploaded_file = st.sidebar.file_uploader("Upload your JSON file", type=["json"])

def get_encoded_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

if uploaded_file is not None:
    try:
        data = json.load(uploaded_file)
        sensor_data = data.get("sensor_data", [])
        plant_data = data.get("plant_data", [])

        st.success("File successfully loaded!")

        # --- Create Map for Harmful Plants ---
        st.subheader("Map: Harmful Plants")
        
        if plant_data:
            valid_plant_coords = [
                (item["latitude"], item["longitude"]) for item in plant_data
                if item.get("latitude") is not None and item.get("longitude") is not None
            ]
            avg_lat = sum(lat for lat, _ in valid_plant_coords) / len(valid_plant_coords) if valid_plant_coords else 0
            avg_lon = sum(lon for _, lon in valid_plant_coords) / len(valid_plant_coords) if valid_plant_coords else 0
        else:
            avg_lat, avg_lon = 0, 0

        plant_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)

        for plant in plant_data:
            lat = plant.get("latitude")
            lon = plant.get("longitude")
            image_path = plant.get("image_path", "")
            species_predictions = ", ".join(sp.get("species", "Unknown") for sp in plant.get("species_predictions", []))
            custom_predictions = ", ".join(pred.get("classification", "Unknown") for pred in plant.get("custom_predictions", []))
            harmful = any(pred.get("plant_status", "").lower() == "harmful" for pred in plant.get("custom_predictions", []))
            
            if harmful:
                img_base64 = get_encoded_image(image_path)
                image_html = f'<img src="data:image/png;base64,{img_base64}" width="150" height="150"><br>' if img_base64 else ""

                popup_text = (
                    f"{image_html}"
                    f"<b>Species:</b> {species_predictions}<br>"
                    f"<b>Classifications:</b> {custom_predictions}<br>"
                    f"(Harmful)"
                )
                popup = folium.Popup(popup_text, max_width=300)
                folium.Marker(
                    location=[lat, lon],
                    popup=popup,
                    icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa")
                ).add_to(plant_map)

        st_folium(plant_map, width=1000, height=750)

        # --- Create Heatmap for Sensor Data ---
        st.subheader("Map: Sensor Data Heatmap (NPK values)")
        
        if sensor_data:
            valid_sensor_coords = [
                (item["latitude"], item["longitude"]) for item in sensor_data
                if item.get("latitude") is not None and item.get("longitude") is not None
            ]
            avg_lat = sum(lat for lat, _ in valid_sensor_coords) / len(valid_sensor_coords) if valid_sensor_coords else 0
            avg_lon = sum(lon for _, lon in valid_sensor_coords) / len(valid_sensor_coords) if valid_sensor_coords else 0
            
            sensor_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)
            heat_data = [
                [sensor["latitude"], sensor["longitude"], sensor.get("npk", 0)] for sensor in sensor_data
                if sensor.get("latitude") is not None and sensor.get("longitude") is not None
            ]
            HeatMap(heat_data, radius=15, blur=10, min_opacity=0.2, max_zoom=18).add_to(sensor_map)
            st_folium(sensor_map, width=700, height=500)
        else:
            st.warning("No sensor data found in the uploaded file.")

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
else:
    st.info("Awaiting JSON file upload. (See sidebar)")
