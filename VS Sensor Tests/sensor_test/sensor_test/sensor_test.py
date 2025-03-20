import serial
import time

# COM Port Configuration
COM_PORT = "COM3"
BAUD_RATE = 4800

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
    if register_address in [TEMP, MOIST, PH]:  # Divide by 10 for some values
        return raw_value / 10.0
    return raw_value

def poll_sensor(ser, address):
    """Send a Modbus request and receive a response"""
    request = [0x01, 0x03, 0x00, address, 0x00, 0x01]  # Modbus request
    request += list(calculate_crc(request))  # Append CRC

    ser.write(bytearray(request))  # Send request
    time.sleep(0.5)  # Wait for response
    response = ser.read(7)  # Expecting 7-byte response

    if len(response) == 7 and response[1] == 0x03:  # Valid response check
        return parse_response(address, response)
    return None

def main():
    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {COM_PORT} at {BAUD_RATE} baud.")

        with open("sensor_data.txt", "a") as outFile:
            while True:
                user_input = input("\nPress ENTER to poll sensors or type 'exit' to quit: ").strip()
                
                if user_input.lower() == "exit":
                    print("Exiting program...")
                    break
                
                elif user_input == "":  # ENTER key pressed
                    print("\nReading sensor data...")
                    outFile.write("\nNew Data Poll:\n")

                    for sensor in DATA_CODES:
                        value = poll_sensor(ser, sensor)
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
                            print(f"{label}: {value}")
                            outFile.write(f"{label}: {value}\n")
                        else:
                            print(f"Error reading {sensor}")

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
