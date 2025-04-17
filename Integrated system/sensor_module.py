import serial
import time
import json

# COM Port Configuration
COM_PORT = "/dev/ttyUSB1"
BAUD_RATE = 4800

# Sensor Device Addresses
SENSOR_1_ID = 0x01  # First sensor address
SENSOR_2_ID = 0x02  # Second sensor address

# Sensor Data Addresses
MOIST = 0x00
TEMP = 0x01
COND = 0x02
PH = 0x03
N = 0x04
P = 0x05
K = 0x06

DATA_CODES = [MOIST, TEMP, COND, PH, N, P, K]

def calculate_crc(data):
    """Calculate CRC-16 (Modbus)"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, 'little')  # Return CRC as little-endian byte pair

def parse_response(register_address, response):
    """Extract and convert sensor data from response"""
    if len(response) < 5:
        return None  # Invalid response

    raw_value = (response[3] << 8) | response[4]  # Combine bytes
    if register_address in [TEMP, MOIST]:  # Divide by 10 for some values
        return raw_value / 10.0
    elif register_address == PH:  # Proper hex to decimal conversion for pH
        return int(response[3] << 8 | response[4]) / 10.0
    return raw_value

def poll_sensor(ser, sensor_id, address):
    """Send a Modbus request to a sensor and receive a response"""
    request = [sensor_id, 0x03, 0x00, address, 0x00, 0x01]  # Modbus request
    request += list(calculate_crc(request))  # Append CRC

    ser.write(bytearray(request))  # Send request
    time.sleep(0.5)  # Wait for response
    response = ser.read(7)  # Expecting 7-byte response

    if len(response) == 7 and response[1] == 0x03:  # Valid response check
        return parse_response(address, response)
    return None

def poll_all_sensors(ser, sensor_id):
    """Poll all data registers for a given sensor"""
    sensor_data = {
        "GPS": {"latitude": None, "longitude": None}  # Blank GPS fields
    }
    for sensor in DATA_CODES:
        value = poll_sensor(ser, sensor_id, sensor)
        if value is not None:
            labels = {
                TEMP: "Temperature (C)",
                MOIST: "Moisture (%)",
                COND: "Conductivity (uS/cm)",
                PH: "pH Level",
                N: "Nitrogen (ppm)",
                P: "Phosphorus (ppm)",
                K: "Potassium (ppm)"
            }
            label = labels.get(sensor, f"Sensor {sensor}")
            sensor_data[label] = value
        else:
            print(f"Error reading {sensor} from Sensor {sensor_id}")
    return sensor_data

def append_results_to_json(sensor1_data, sensor2_data):
    """Append new soil sensor data to a JSON file"""
    try:
        with open("soil_data.json", "r") as json_file:
            data = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {"soil_results": []}  # Create new structure if file doesn't exist or is corrupted

    # Append new data entry with timestamp
    new_entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "sensor_1": sensor1_data,
        "sensor_2": sensor2_data
    }
    data["soil_results"].append(new_entry)

    with open("soil_data.json", "w") as json_file:
        json.dump(data, json_file, indent=4)

def main():
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {COM_PORT} at {BAUD_RATE} baud.")

        while True:
            user_input = input("\nPress ENTER to poll sensors or type 'exit' to quit: ").strip()
            
            if user_input.lower() == "exit":
                print("Exiting program...")
                break
            
            elif user_input == "":  # ENTER key pressed
                print("\nReading sensor data...")

                # Poll Sensor 1
                print("\nSensor 1 Data:")
                sensor1_data = poll_all_sensors(ser, SENSOR_1_ID)
                for label, value in sensor1_data.items():
                    print(f"{label}: {value}")

                # Poll Sensor 2
                print("\nSensor 2 Data:")
                sensor2_data = poll_all_sensors(ser, SENSOR_2_ID)
                for label, value in sensor2_data.items():
                    print(f"{label}: {value}")

                # Append results to JSON file
                append_results_to_json(sensor1_data, sensor2_data)
                print("\nData appended to soil_data.json\n")

    except serial.SerialException as e:
        print(f"Serial port error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if ser:
            ser.close()
            print("Serial port closed.")

if __name__ == "__main__":
    main()