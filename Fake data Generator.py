import csv
import random

# File name
data_file = "sensor_data.csv"

# Generate fake sensor data
with open(data_file, "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Latitude", "Longitude", "N", "P", "K", "pH", "Temperature", "Moisture", "Harmful"])  # Column headers
    
    for _ in range(50):  # Generate 50 sample data points
        lat = 51.5 + random.uniform(-0.01, 0.01)
        lon = -0.12 + random.uniform(-0.01, 0.01)
        nitrogen = random.uniform(0, 100)
        phosphorus = random.uniform(0, 100)
        potassium = random.uniform(0, 100)
        pH = random.uniform(4, 9)
        temperature = random.uniform(10, 35)
        moisture = random.uniform(0, 100)
        harmful = random.choice([0, 1])  # 0 = Not harmful, 1 = Harmful
        
        writer.writerow([lat, lon, nitrogen, phosphorus, potassium, pH, temperature, moisture, harmful])

print(f"Fake data saved to {data_file}")