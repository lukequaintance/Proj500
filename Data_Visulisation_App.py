import os
import sys
import json
import base64
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# -----------------------------------------------------------
# Launch Streamlit App (if not already launched)
# -----------------------------------------------------------
if not os.environ.get("STREAMLIT_STARTED"):
    # Set an environment variable to indicate the app has started
    os.environ["STREAMLIT_STARTED"] = "1"
    # Launch the app using Streamlit and exit this instance
    os.system("python -m streamlit run Data_Visulisation_App.py")
    sys.exit()

# -----------------------------------------------------------
# Set up the Streamlit page configuration
# -----------------------------------------------------------
st.set_page_config(page_title="Field Data Visualization", layout="wide")
st.title("Field Data Visualization Application")

# -----------------------------------------------------------
# Sidebar: File Upload
# -----------------------------------------------------------
st.sidebar.header("Data Upload")
uploaded_file = st.sidebar.file_uploader("Upload your JSON file", type=["json"])

# -----------------------------------------------------------
# Function to encode an image file in base64 for embedding in HTML
# -----------------------------------------------------------
def get_encoded_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

# -----------------------------------------------------------
# Process the uploaded JSON file (if any)
# -----------------------------------------------------------
if uploaded_file is not None:
    try:
        # Load the JSON data
        data = json.load(uploaded_file)
        sensor_data = data.get("sensor_data", [])
        plant_data = data.get("plant_data", [])
        st.success("File successfully loaded!")

        # -----------------------------------------------------------
        # Process Plant Data
        # -----------------------------------------------------------
        harmful_valid = []         # Harmful plants with valid GPS data
        harmful_missing_gps = []   # Harmful plants missing GPS data
        nonharmful_valid = []      # Non-harmful plants with valid GPS data

        for plant in plant_data:
            lat = plant.get("latitude")
            lon = plant.get("longitude")
            # Check if the plant is marked as harmful based on custom_predictions
            harmful = any(
                pred.get("plant_status", "").lower() == "harmful" 
                for pred in plant.get("custom_predictions", [])
            )
            if harmful:
                if lat is not None and lon is not None:
                    harmful_valid.append(plant)
                else:
                    harmful_missing_gps.append(plant)
            else:
                # Only add non-harmful plants if valid GPS data exists
                if lat is not None and lon is not None:
                    nonharmful_valid.append(plant)

        # -----------------------------------------------------------
        # Create Map for Plants with Valid GPS Data
        # -----------------------------------------------------------
        st.subheader("Map: Plants with GPS Data")
        # Combine coordinates of both harmful and non-harmful plants
        valid_coords = [
            (plant["latitude"], plant["longitude"])
            for plant in harmful_valid + nonharmful_valid
        ]
        # Calculate average latitude and longitude to center the map
        if valid_coords:
            avg_lat = sum(lat for lat, _ in valid_coords) / len(valid_coords)
            avg_lon = sum(lon for _, lon in valid_coords) / len(valid_coords)
        else:
            avg_lat, avg_lon = 0, 0

        # Create a Folium map centered at the calculated average coordinates
        plant_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)

        # -----------------------------------------------------------
        # Add Markers for Harmful Plants (Red Markers)
        # -----------------------------------------------------------
        for plant in harmful_valid:
            lat = plant["latitude"]
            lon = plant["longitude"]
            image_path = plant.get("image_path", "")
            # Get species predictions and custom predictions as comma-separated strings
            species_predictions = ", ".join(
                sp.get("species", "Unknown") for sp in plant.get("species_predictions", [])
            )
            custom_predictions = ", ".join(
                pred.get("classification", "Unknown") for pred in plant.get("custom_predictions", [])
            )
            # Get the base64 encoded image if available
            img_base64 = get_encoded_image(image_path)
            image_html = (
                f'<img src="data:image/png;base64,{img_base64}" width="150" height="150"><br>'
                if img_base64 else ""
            )
            # Create popup HTML with image and predictions
            popup_text = (
                f"{image_html}"
                f"<b>Species:</b> {species_predictions}<br>"
                f"<b>Classifications:</b> {custom_predictions}<br>"
                f"(Harmful)"
            )
            popup = folium.Popup(popup_text, max_width=300)
            # Add a red marker to the map
            folium.Marker(
                location=[lat, lon],
                popup=popup,
                icon=folium.Icon(color="red", icon="exclamation-triangle", prefix="fa")
            ).add_to(plant_map)

        # -----------------------------------------------------------
        # Add Markers for Non-Harmful Plants (Green Markers)
        # -----------------------------------------------------------
        for plant in nonharmful_valid:
            lat = plant["latitude"]
            lon = plant["longitude"]
            image_path = plant.get("image_path", "")
            # Get species and custom predictions as comma-separated strings
            species_predictions = ", ".join(
                sp.get("species", "Unknown") for sp in plant.get("species_predictions", [])
            )
            custom_predictions = ", ".join(
                pred.get("classification", "Unknown") for pred in plant.get("custom_predictions", [])
            )
            # Get the base64 encoded image if available
            img_base64 = get_encoded_image(image_path)
            image_html = (
                f'<img src="data:image/png;base64,{img_base64}" width="150" height="150"><br>'
                if img_base64 else ""
            )
            # Create popup HTML with image and predictions
            popup_text = (
                f"{image_html}"
                f"<b>Species:</b> {species_predictions}<br>"
                f"<b>Classifications:</b> {custom_predictions}<br>"
                f"(Non-Harmful)"
            )
            popup = folium.Popup(popup_text, max_width=300)
            # Add a green marker to the map
            folium.Marker(
                location=[lat, lon],
                popup=popup,
                icon=folium.Icon(color="green", icon="leaf", prefix="fa")
            ).add_to(plant_map)

        # Render the plant map using Streamlit-Folium
        st_folium(plant_map, width=1000, height=750)

        # -----------------------------------------------------------
        # Display Harmful Plants that are Missing GPS Data
        # -----------------------------------------------------------
        if harmful_missing_gps:
            st.subheader("Harmful Plants Missing GPS Data")
            st.info("The following harmful plants were not plotted on the map because they are missing GPS data:")
            for idx, plant in enumerate(harmful_missing_gps, start=1):
                species_predictions = ", ".join(
                    sp.get("species", "Unknown") for sp in plant.get("species_predictions", [])
                )
                custom_predictions = ", ".join(
                    pred.get("classification", "Unknown") for pred in plant.get("custom_predictions", [])
                )
                st.markdown(
                    f"**Plant {idx}:** Species: {species_predictions} | Classifications: {custom_predictions}"
                )

        # -----------------------------------------------------------
        # Create Heatmap for Sensor Data (NPK values)
        # -----------------------------------------------------------
        st.subheader("Map: Sensor Data Heatmap (NPK values)")
        if sensor_data:
            # Filter out sensor data with valid GPS coordinates
            valid_sensor_coords = [
                (item["latitude"], item["longitude"])
                for item in sensor_data
                if item.get("latitude") is not None and item.get("longitude") is not None
            ]
            # Calculate the average coordinates for centering the map
            if valid_sensor_coords:
                avg_lat = sum(lat for lat, _ in valid_sensor_coords) / len(valid_sensor_coords)
                avg_lon = sum(lon for _, lon in valid_sensor_coords) / len(valid_sensor_coords)
            else:
                avg_lat, avg_lon = 0, 0

            # Create a Folium map for sensor data heatmap
            sensor_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)
            heat_data = [
                [sensor["latitude"], sensor["longitude"], sensor.get("npk", 0)]
                for sensor in sensor_data
                if sensor.get("latitude") is not None and sensor.get("longitude") is not None
            ]
            # Add a heatmap layer using sensor data
            HeatMap(heat_data, radius=15, blur=10, min_opacity=0.2, max_zoom=18).add_to(sensor_map)
            st_folium(sensor_map, width=700, height=500)
        else:
            st.warning("No sensor data found in the uploaded file.")

        # -----------------------------------------------------------
        # Create Heatmaps for Soil Sensor Data (Individual Parameters)
        # -----------------------------------------------------------
        soil_results = data.get("soil_results", [])
        if soil_results:
            st.subheader("Soil Sensor Data Heatmaps")
            # Let the user select which sensor(s) to display
            sensors_to_show = st.multiselect("Select sensor data to display",
                                             options=["Sensor 1", "Sensor 2"],
                                             default=["Sensor 1", "Sensor 2"])
            # List of parameters to create individual heatmaps for
            parameters = [
                "Moisture (%)", "Temperature (C)", "Conductivity (uS/cm)",
                "pH Level", "Nitrogen (ppm)", "Phosphorus (ppm)", "Potassium (ppm)"
            ]
            # Create a separate tab for each parameter
            tabs = st.tabs(parameters)
            for param, tab in zip(parameters, tabs):
                with tab:
                    heat_data = []
                    # Loop over each soil result and each selected sensor
                    for result in soil_results:
                        for sensor in sensors_to_show:
                            sensor_key = "sensor_1" if sensor == "Sensor 1" else "sensor_2"
                            sensor_item = result.get(sensor_key, {})
                            gps = sensor_item.get("GPS", {})
                            lat = gps.get("latitude")
                            lon = gps.get("longitude")
                            value = sensor_item.get(param)
                            # Only add data points with valid GPS and a non-null parameter value
                            if lat is not None and lon is not None and value is not None:
                                heat_data.append([lat, lon, value])
                    # Determine the center of the map if there are valid data points
                    if heat_data:
                        avg_lat = sum(point[0] for point in heat_data) / len(heat_data)
                        avg_lon = sum(point[1] for point in heat_data) / len(heat_data)
                    else:
                        avg_lat, avg_lon = 0, 0
                    # Create a Folium map and add the heatmap layer
                    soil_map = folium.Map(location=[avg_lat, avg_lon], zoom_start=13)
                    HeatMap(heat_data, radius=15, blur=10, min_opacity=0.2, max_zoom=18).add_to(soil_map)
                    st_folium(soil_map, width=700, height=500)
        else:
            st.info("No soil sensor data found in the uploaded file.")

    except Exception as e:
        st.error(f"An error occurred while processing the file: {e}")
else:
    st.info("Awaiting JSON file upload. (See sidebar)")
