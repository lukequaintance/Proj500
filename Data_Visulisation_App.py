import os
import sys
import json
import base64
import streamlit as st
import folium
from streamlit_folium import st_folium
import branca.colormap as cm  # For linear colormap

# -----------------------------------------------------------
# Launch Streamlit App (if not already launched)
# -----------------------------------------------------------
if not os.environ.get("STREAMLIT_STARTED"):
    os.environ["STREAMLIT_STARTED"] = "1"
    os.system("python -m streamlit run Data_Visulisation_App.py")
    sys.exit()

# -----------------------------------------------------------
# Streamlit Page Configuration
# -----------------------------------------------------------
st.set_page_config(page_title="Field Data Visualization", layout="wide")
st.title("Field Data Visualization Application")

# -----------------------------------------------------------
# Sidebar: File Uploads and Filters
# -----------------------------------------------------------
st.sidebar.header("Data Upload & Filters")
uploaded_file_plant = st.sidebar.file_uploader("Upload Plant Data JSON", type=["json"], key="plant_file")
# Slider for minimum species confidence filter
min_confidence_percentage = st.sidebar.slider(
    "Minimum species confidence to display (%)", 0, 100, 0, step=1, key="min_confidence_percentage"
)
min_confidence = min_confidence_percentage / 100  # Convert percentage to decimal
uploaded_file_soil = st.sidebar.file_uploader("Upload Soil Data JSON", type=["json"], key="soil_file")



# -----------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------
def get_encoded_image(image_path):
    """Encode an image to base64 for display in HTML."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except FileNotFoundError:
        return None

def compute_bounds(coords):
    """Compute map bounds from a list of coordinates."""
    if not coords:
        return [[0, 0], [0, 0]]
    lats = [lat for lat, lon in coords]
    lons = [lon for lat, lon in coords]
    return [[min(lats), min(lons)], [max(lats), max(lons)]]

def compute_center(coords):
    """Compute the center of a list of coordinates."""
    if coords:
        avg_lat = sum(lat for lat, lon in coords) / len(coords)
        avg_lon = sum(lon for lat, lon in coords) / len(coords)
        return [avg_lat, avg_lon]
    return [0, 0]

# -----------------------------------------------------------
# Process Plant Data
# -----------------------------------------------------------
global_coords = []
plant_data = []
if uploaded_file_plant is not None:
    try:
        data = json.load(uploaded_file_plant)
        plant_data = data.get("plant_data", [])
        st.success("Plant Data file loaded")

        harmful_valid = []
        harmful_missing_gps = []
        nonharmful_valid = []

        # Process each plant entry
        for plant in plant_data:
            try:
                lat = float(plant.get("latitude"))
                lon = float(plant.get("longitude"))
            except (TypeError, ValueError):
                lat = lon = None

            harmful = any(pred.get("plant_status", "").lower() == "harmful"
                          for pred in plant.get("custom_predictions", []))

            target_list = harmful_valid if harmful else nonharmful_valid
            missing_list = harmful_missing_gps if harmful and (lat is None or lon is None) else None

            if lat is not None and lon is not None:
                target_list.append(plant)
                global_coords.append((lat, lon))
            elif missing_list is not None:
                missing_list.append(plant)

        # Plot plants on the map
        st.subheader("Map: Harmful Plants")
        plant_map = folium.Map()

        def plot_plants(plants, color, icon, status_label):
            """Plot plants on the map with specific markers."""
            for plant in plants:
                preds = [sp for sp in plant.get("species_predictions", [])
                         if sp.get("confidence", 0) >= min_confidence]
                if not preds:
                    continue
                lat = float(plant.get("latitude"))
                lon = float(plant.get("longitude"))
                img_html = ''
                img_path = plant.get("image_path", "")
                img64 = get_encoded_image(img_path)
                if img64:
                    img_html = f'<img src="data:image/png;base64,{img64}" width="150" height="150"><br>'
                species_list = ", ".join(
                    f"{sp['species']} ({sp['confidence']:.2f})" for sp in preds
                )
                custom_list = ", ".join(
                    pred.get("classification", "Unknown") for pred in plant.get("custom_predictions", [])
                )
                popup_html = (
                    f"{img_html}"
                    f"<b>Species:</b> {species_list}<br>"
                    f"<b>Classifications:</b> {custom_list}<br>"
                    f"({status_label})"
                )
                popup = folium.Popup(popup_html, max_width=400)
                folium.Marker(
                    location=[lat, lon],
                    popup=popup,
                    icon=folium.Icon(color=color, icon=icon, prefix="fa")
                ).add_to(plant_map)

        plot_plants(harmful_valid, "red", "exclamation-triangle", "Harmful")
        plot_plants(nonharmful_valid, "green", "leaf", "Non-Harmful")

        plant_map.fit_bounds(compute_bounds(global_coords))
        st_folium(plant_map, use_container_width=True, height=500)

        # Display harmful plants missing GPS
        if harmful_missing_gps:
            st.subheader("Harmful Plants Missing GPS")
            for i, plant in enumerate(harmful_missing_gps, 1):
                species_list = ", ".join(
                    sp.get("species", "Unknown") for sp in plant.get("species_predictions", [])
                )
                st.markdown(f"**{i}.** Species: {species_list}")

    except Exception as e:
        st.error(f"Error processing plant data: {e}")
else:
    st.info("Upload Plant Data JSON in sidebar.")

# -----------------------------------------------------------
# Process Soil Data
# -----------------------------------------------------------
if uploaded_file_soil is not None:
    try:
        soil_data = json.load(uploaded_file_soil)
        soil_results = soil_data.get("soil_results", [])
        st.success("Soil Data file successfully loaded!")

        # Extract soil sensor coordinates
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

        # Define soil parameters and thresholds
        parameters = [
            "Moisture (%)", "Temperature (C)", "Conductivity (uS/cm)",
            "pH Level", "Nitrogen (ppm)", "Phosphorus (ppm)", "Potassium (ppm)"
        ]
        st.sidebar.subheader("Sensor Discrepancy Thresholds")
        default_thresholds = {
            "Moisture (%)": 10.0,
            "Temperature (C)": 2.0,
            "Conductivity (uS/cm)": 410.0,
            "pH Level": 0.5,
            "Nitrogen (ppm)": 85.0,
            "Phosphorus (ppm)": 200.0,
            "Potassium (ppm)": 200.0
        }
        hazard_thresholds = {
            param: st.sidebar.number_input(
            f"Set hazard threshold for {param} difference",
            value=default_thresholds.get(param, 50.0),
            step={
                "Moisture (%)": 1.0,
                "Temperature (C)": 0.1,
                "Conductivity (uS/cm)": 10.0,
                "pH Level": 0.1,
                "Nitrogen (ppm)": 5.0,
                "Phosphorus (ppm)": 10.0,
                "Potassium (ppm)": 10.0
            }.get(param, 1.0),
            min_value=0.0, key=f"hazard_{param.replace(' ', '_')}"
            )
            for param in parameters
        }

        # Multiselect for soil parameters to display
        selected_parameters = st.multiselect("Select soil parameter(s) to display",
                                             options=parameters, default=[], key="soil_parameter_select")
        if selected_parameters:
            num_cols = 2
            columns = st.columns(num_cols)  # Create columns for maps

            for i, param in enumerate(selected_parameters):
                col = columns[i % num_cols]
                with col:
                    col.markdown(f"#### {param}")

                    # Extract min/max values for the parameter
                    all_values = [
                        float(result.get(sensor, {}).get(param))
                        for result in soil_results
                        for sensor in ["sensor_1", "sensor_2"]
                        if result.get(sensor, {}).get(param) is not None
                    ]
                    data_min, data_max = (min(all_values), max(all_values)) if all_values else (0, 100)

                    # Create colormap
                    param_colormap = cm.LinearColormap(
                        colors=['blue', 'cyan', 'lime', 'yellow', 'orange', 'red'],
                        vmin=data_min, vmax=data_max
                    )

                    # Create map for the parameter
                    param_map = folium.Map(location=overall_soil_center, zoom_start=13)
                    for result in soil_results:
                        timestamp = result.get("timestamp", "N/A")
                        sensor1 = result.get("sensor_1", {})
                        sensor2 = result.get("sensor_2", {})
                        gps1 = sensor1.get("GPS", {})
                        gps2 = sensor2.get("GPS", {})

                        try:
                            lat = float(gps1.get("latitude")) if gps1.get("latitude") else float(gps2.get("latitude"))
                            lon = float(gps1.get("longitude")) if gps1.get("longitude") else float(gps2.get("longitude"))
                        except (TypeError, ValueError):
                            continue

                        val1 = sensor1.get(param)
                        val2 = sensor2.get(param)
                        avg_val = (float(val1) + float(val2)) / 2 if val1 and val2 else float(val1 or val2)
                        diff = abs(float(val1 or 0) - float(val2 or 0)) if val1 and val2 else 0

                        color = param_colormap(avg_val)
                        popup_text = f"<b>{param} Readings</b><br>Timestamp: {timestamp}<br>"
                        if val1:
                            popup_text += f"Sensor 1: {val1}<br>"
                        if val2:
                            popup_text += f"Sensor 2: {val2}<br>"
                        if val1 and val2:
                            popup_text += f"<span style='color:red;'><b>Difference: {diff:.2f}</b></span><br>"

                        if val1 and val2 and diff > hazard_thresholds[param]:
                            folium.Marker(
                                location=[lat, lon],
                                popup=folium.Popup(popup_text, max_width=400),
                                icon=folium.Icon(color='red', icon='exclamation-triangle', prefix='fa')
                            ).add_to(param_map)
                        else:
                            folium.CircleMarker(
                                location=[lat, lon],
                                radius=8,
                                fill=True,
                                fill_color=color,
                                color=color,
                                fill_opacity=0.8,
                                tooltip=popup_text
                            ).add_to(param_map)

                    st_folium(param_map, use_container_width=True, height=500, key=f"{param}_map")

        else:
            st.info("No soil parameters selected.")
    except Exception as e:
        st.error(f"An error occurred while processing the Soil Data file: {e}")
else:
    st.info("Awaiting Soil Data JSON file upload. (See sidebar)")
