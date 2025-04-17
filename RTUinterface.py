from pymavlink import mavutil

# Set up the serial connection with the COM port 3
# Parameters: COM port 3, baud rate 115200, 8N1 (8 data bits, no parity, 1 stop bit)
connection = mavutil.mavlink_connection('COM3', baud=115200, source_system=1, source_component=1)

# Wait for the heartbeat message to confirm the connection
connection.wait_heartbeat()
print("Heartbeat from system (system ID %u component ID %u)" % (connection.target_system, connection.target_component))

# Start receiving and printing messages
# Start receiving and filtering specific data (GPS_RAW_INT)
while True:
    msg = connection.recv_match(blocking=True)
    if msg and msg.get_type() == 'GPS_RAW_INT':
        gps_data = msg.to_dict()  # Convert message to a dictionary for easy access
        print("GPS Data:")
        print(f"Latitude: {gps_data['lat']}")
        print(f"Longitude: {gps_data['lon']}")
        print(f"Altitude: {gps_data['alt']}")
        print(f"Fix Type: {gps_data['fix_type']}")
