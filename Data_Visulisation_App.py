import os
import sys
import json
import base64
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import branca.colormap as cm  # Import for linear colormap

# -----------------------------------------------------------
# Launch Streamlit App (if not already launched)
# -----------------------------------------------------------
if not os.environ.get("STREAMLIT_STARTED"):
    os.environ["STREAMLIT_STARTED"] = "1"
    os.system("python -m streamlit run Data_Visulisation_App.py")
    sys.exit()

# -----------------------------------------------------------
# Set up the Streamlit page configuration
# -----------------------------------------------------------
st.set_page_config(page_title="Field Data Visualization", layout="wide")
st.title("Field Data Visualization Application")

# -----------------------------------------------------------
# Sidebar: File Uploads and Hazard Threshold Input
# -----------------------------------------------------------
st.sidebar.header("Data Upload")
# File for plant data (and its associated sensor data if any)
uploaded_file_plant = st.sidebar.file_uploader("Upload your Plant Data JSON file", type=["json"], key="plant_file")
# File for soil sensor data
uploaded_file_soil = st.sidebar.file_uploader("Upload your Soil Data JSON file", type=["json"], key="soil_file")

# Global list to store all valid coordinates (from plant and soil data)
global_coords = []

# -----------------------------------------------------------
# Function to encode an image file in base64 for embedding in HTML
# -----------------------------------------------------------
def get_encoded_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

# Function to compute bounding box from a list of (lat,lon) tuples
def compute_bounds(coords):
    if not coords:
        return [[0, 0], [0, 0]]
    lats = [float(lat) for lat, lon in coords]
    lons = [float(lon) for lat, lon in coords]
    return [[min(lats), min(lons)], [max(lats), max(lons)]]

# Function to compute center (average) from coordinates
def compute_center(coords):
    if coords:
        avg_lat = sum(float(lat) for lat, lon in coords) / len(coords)
        avg_lon = sum(float(lon) for lat, lon in coords) / len(coords)
        return [avg_lat, avg_lon]
    return [0, 0]

# Define acceptable thresholds for each soil parameter (adjust as needed)
thresholds = {
    "Moisture (%)": (40, 90),          # Adjusted range
    "Temperature (C)": (10, 40),       # Adjusted range
    "Conductivity (uS/cm)": (3000, 8000), # Adjusted range
    "pH Level": (40, 100),             # Adjusted range
    "Nitrogen (ppm)": (1000, 3000),    # Adjusted range
    "Phosphorus (ppm)": (1000, 3000),   # Adjusted range
    "Potassium (ppm)": (1000, 4000)     # Adjusted range
}

# Define a common gradient (kept here in case it is needed elsewhere)
gradient = {'0.0': 'blue', '0.5': 'lime', '1.0': 'red'}

# Placeholder for plant_data to be used later if needed
plant_data = []

# -----------------------------------------------------------
# Process the Plant Data file (if any)
# -----------------------------------------------------------
if uploaded_file_plant is not None:
    try:
        data = json.load(uploaded_file_plant)
        plant_data = data.get("plant_data", [])
        st.success("Plant Data file successfully loaded!")

        # Process Plant Data
        harmful_valid = []         # Harmful plants with valid GPS data
        harmful_missing_gps = []   # Harmful plants missing GPS data
        nonharmful_valid = []      # Non-harmful plants with valid GPS data

        for plant in plant_data:
            try:
                lat = float(plant.get("latitude"))
                lon = float(plant.get("longitude"))
            except (TypeError, ValueError):
                lat = lon = None

            harmful = any(
                pred.get("plant_status", "").lower() == "harmful" 
                for pred in plant.get("custom_predictions", [])
            )
            if harmful:
                if lat is not None and lon is not None:
                    harmful_valid.append(plant)
                    global_coords.append((lat, lon))
                else:
                    harmful_missing_gps.append(plant)
            else:
                if lat is not None and lon is not None:
                    nonharmful_valid.append(plant)
                    global_coords.append((lat, lon))

        # Create Map for Plants with Valid GPS Data
        st.subheader("Map: Plants with GPS Data")
        plant_map = folium.Map()
        # Add markers for harmful plants (red)
        for plant in harmful_valid:
            lat = float(plant.get("latitude"))
            lon = float(plant.get("longitude"))
            image_path = plant.get("image_path", "")
            species_predictions = ", ".join(
                sp.get("species", "Unknown") for sp in plant.get("species_predictions", [])
            )
            custom_predictions = ", ".join(
                pred.get("classification", "Unknown") for pred in plant.get("custom_predictions", [])
            )
            img_base64 = get_encoded_image(image_path)
            image_html = (
                f'<img src="data:image/png;base64,{img_base64}" width="150" height="150"><br>'
                if img_base64 else ""
            )
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
        # Add markers for non-harmful plants (green)
        for plant in nonharmful_valid:
            lat = float(plant.get("latitude"))
            lon = float(plant.get("longitude"))
            image_path = plant.get("image_path", "")
            species_predictions = ", ".join(
                sp.get("species", "Unknown") for sp in plant.get("species_predictions", [])
            )
            custom_predictions = ", ".join(
                pred.get("classification", "Unknown") for pred in plant.get("custom_predictions", [])
            )
            img_base64 = get_encoded_image(image_path)
            image_html = (
                f'<img src="data:image/png;base64,{img_base64}" width="150" height="150"><br>'
                if img_base64 else ""
            )
            popup_text = (
                f"{image_html}"
                f"<b>Species:</b> {species_predictions}<br>"
                f"<b>Classifications:</b> {custom_predictions}<br>"
                f"(Non-Harmful)"
            )
            popup = folium.Popup(popup_text, max_width=300)
            folium.Marker(
                location=[lat, lon],
                popup=popup,
                icon=folium.Icon(color="green", icon="leaf", prefix="fa")
            ).add_to(plant_map)
        # Center plant map over provided plant data
        plant_bounds = compute_bounds(global_coords)
        plant_map.fit_bounds(plant_bounds)
        st_folium(plant_map, width=1000, height=750, key="plant_map")

        # Display info for plants missing GPS
        if harmful_missing_gps:
            st.subheader("Harmful Plants Missing GPS Data")
            st.info("The following harmful plants were not plotted because they are missing GPS data:")
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

    except Exception as e:
        st.error(f"An error occurred while processing the Plant Data file: {e}")
else:
    st.info("Awaiting Plant Data JSON file upload. (See sidebar)")

# -----------------------------------------------------------
# Process the Soil Data file (if any)
# -----------------------------------------------------------
if uploaded_file_soil is not None:
    try:
        soil_data = json.load(uploaded_file_soil)
        soil_results = soil_data.get("soil_results", [])
        st.success("Soil Data file successfully loaded!")

        # Create a list for soil sensor coordinates only
        soil_coords = []
        for result in soil_results:
            for sensor_key in ["sensor_1", "sensor_2"]:
                sensor_item = result.get(sensor_key, {})
                gps = sensor_item.get("GPS", {})
                try:
                    lat = float(gps.get("latitude"))
                    lon = float(gps.get("longitude"))
                    soil_coords.append((lat, lon))
                except (TypeError, ValueError):
                    continue
        overall_soil_center = compute_center(soil_coords)

        # Define soil parameters
        parameters = [
            "Moisture (%)", "Temperature (C)", "Conductivity (uS/cm)",
            "pH Level", "Nitrogen (ppm)", "Phosphorus (ppm)", "Potassium (ppm)"
        ]

        st.sidebar.subheader("Sensor Discrepancy Thresholds")

        # Define hazard threshold inputs individually
        hazard_moisture = st.sidebar.number_input(
            "Set hazard threshold for Moisture (%) difference",
            value=5.0, step=1.0, min_value=0.0, key="hazard_Moisture"
        )

        hazard_temperature = st.sidebar.number_input(
            "Set hazard threshold for Temperature (C) difference",
            value=3.0, step=1.0, min_value=0.0, key="hazard_Temperature"
        )

        hazard_conductivity = st.sidebar.number_input(
            "Set hazard threshold for Conductivity (uS/cm) difference",
            value=50.0, step=10.0, min_value=0.0, key="hazard_Conductivity"
        )

        hazard_ph = st.sidebar.number_input(
            "Set hazard threshold for pH Level difference",
            value=10.0, step=1.0, min_value=0.0, key="hazard_pH"
        )

        hazard_nitrogen = st.sidebar.number_input(
            "Set hazard threshold for Nitrogen (ppm) difference",
            value=50.0, step=10.0, min_value=0.0, key="hazard_Nitrogen"
        )

        hazard_phosphorus = st.sidebar.number_input(
            "Set hazard threshold for Phosphorus (ppm) difference",
            value=50.0, step=10.0, min_value=0.0, key="hazard_Phosphorus"
        )

        hazard_potassium = st.sidebar.number_input(
            "Set hazard threshold for Potassium (ppm) difference",
            value=50.0, step=10.0, min_value=0.0, key="hazard_Potassium"
        )

                # Build a dictionary to map each parameter to its hazard threshold value.
        hazard_thresholds = {
            "Moisture (%)": hazard_moisture,
            "Temperature (C)": hazard_temperature,
            "Conductivity (uS/cm)": hazard_conductivity,
            "pH Level": hazard_ph,
            "Nitrogen (ppm)": hazard_nitrogen,
            "Phosphorus (ppm)": hazard_phosphorus,
            "Potassium (ppm)": hazard_potassium
        }

        # Multiselect for soil parameters to display (default empty)
        selected_parameters = st.multiselect("Select soil parameter(s) to display",
                                             options=parameters,
                                             default=[],
                                             key="soil_parameter_select")
        if selected_parameters:
            num_params = len(selected_parameters)
            num_cols = 2
            rows = (num_params + num_cols - 1) // num_cols  # Calculate number of rows
            columns = st.columns(num_cols)  # Create two columns for each row
            
            for i, param in enumerate(selected_parameters):
                col = columns[i % num_cols]  # Assign alternating maps to columns
                with col:
                    col.markdown(f"#### {param}")
                    
                    # Create colormap for this parameter
                    t_min, t_max = thresholds[param]
                    param_colormap = cm.LinearColormap(colors=['blue', 'red'], vmin=t_min, vmax=t_max)

                    # Create a folium map
                    param_map = folium.Map(location=overall_soil_center, zoom_start=13)
                    
                    for result in soil_results:
                        timestamp = result.get("timestamp", "N/A")
                        sensor1 = result.get("sensor_1", {})
                        sensor2 = result.get("sensor_2", {})
                        gps1 = sensor1.get("GPS", {})
                        gps2 = sensor2.get("GPS", {})

                        try:
                            lat = float(gps1.get("latitude")) if gps1.get("latitude") is not None else float(gps2.get("latitude"))
                            lon = float(gps1.get("longitude")) if gps1.get("longitude") is not None else float(gps2.get("longitude"))
                        except (TypeError, ValueError):
                            continue

                        try:
                            val1 = float(sensor1.get(param))
                        except (TypeError, ValueError):
                            val1 = None
                        try:
                            val2 = float(sensor2.get(param))
                        except (TypeError, ValueError):
                            val2 = None

                        if val1 is not None or val2 is not None:
                            if val1 is not None and val2 is not None:
                                avg_val = (val1 + val2) / 2
                                diff = abs(val1 - val2)
                            else:
                                avg_val = val1 if val1 is not None else val2
                                diff = 0
                            color = param_colormap(avg_val)
                            popup_text = f"<b>{param} Readings</b><br>Timestamp: {timestamp}<br>"
                            if val1 is not None:
                                popup_text += f"Sensor 1: {val1:.1f}<br>"
                            if val2 is not None:
                                popup_text += f"Sensor 2: {val2:.1f}<br>"
                            if val1 is not None and val2 is not None and diff > hazard_thresholds[param]:
                                popup_text += f"<span style='color:red;'><b>Discrepancy:</b> Difference between sensors {diff:.1f} </span>"
                            folium.CircleMarker(
                                location=[lat, lon],
                                radius=8,
                                fill=True,
                                fill_color=color,
                                color=color,
                                fill_opacity=0.8,
                                tooltip=popup_text
                            ).add_to(param_map)

                    # Display map in the current column
                    st_folium(param_map, width=500, height=500, key=f"{param}_map")

                # Reset columns every two maps to start a new row
                if (i + 1) % num_cols == 0 and i + 1 < num_params:
                    columns = st.columns(num_cols)  # Create new columns for the next row

        else:
            st.info("No soil parameters selected.")
    except Exception as e:
        st.error(f"An error occurred while processing the Soil Data file: {e}")
else:
    st.info("Awaiting Soil Data JSON file upload. (See sidebar)")