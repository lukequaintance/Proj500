import json
import random

def generate_sensor_data(num_points=1000, center_lat=50.374963, center_lon=-4.094525, spread=0.002):
    """
    Generates simulated sensor data around a given center.
    Default coordinates (50.3755, -4.1427) correspond to a location near Plymouth, England.
    """
    sensor_data = []
    for _ in range(num_points):
        data_point = {
            "latitude": center_lat + random.uniform(-spread, spread),
            "longitude": center_lon + random.uniform(-spread, spread),
            "npk": round(random.uniform(0, 100), 2),      # example NPK value
            "ph": round(random.uniform(5.5, 7.5), 2),       # example soil pH value
            "temperature": round(random.uniform(10, 35), 1),# temperature in Celsius
            "moisture": round(random.uniform(0, 1), 2)      # soil moisture as a fraction (0 to 1)
        }
        sensor_data.append(data_point)
    return sensor_data

def generate_plant_data(num_plants=20, center_lat=50.374963, center_lon=-4.094525, spread=0.002):
    """
    Generates simulated plant data around a given center.
    Default coordinates (50.3755, -4.1427) correspond to a location near Plymouth, England.
    """
    plant_names = ["Dandelion", "Nettles", "Thistle", "Poison Ivy", "Ragweed", "Bindweed"]
    plant_data = []
    for _ in range(num_plants):
        # Randomly select a plant name
        name = random.choice(plant_names)
        # Randomly flag harmful plants (for simulation, assume a 50% chance)
        harmful = random.choice([True, False])
        data_point = {
            "latitude": center_lat + random.uniform(-spread, spread),
            "longitude": center_lon + random.uniform(-spread, spread),
            "plant_name": name,
            "harmful": harmful
        }
        plant_data.append(data_point)
    return plant_data

def main():
    data = {
        "sensor_data": generate_sensor_data(),
        "plant_data": generate_plant_data()
    }
    output_file = "simulated_field_data.json"
    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)
    print(f"Simulated data has been written to {output_file}")

if __name__ == "__main__":
    main()
