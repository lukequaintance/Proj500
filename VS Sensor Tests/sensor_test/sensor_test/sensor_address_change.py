import serial
import time

COM_PORT = "COM9"  # Adjust if needed
BAUD_RATE = 4800

def calculate_crc(data):
    """Calculate CRC-16 for Modbus"""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, 'little')  # Return CRC in little-endian

def change_modbus_address(current_id, new_id):
    """Send Modbus command to change sensor address"""
    request = [current_id, 0x06, 0x07, 0xD0, 0x00, new_id]  # Address change command
    request += list(calculate_crc(request))  # Append CRC

    try:
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        ser.write(bytearray(request))
        time.sleep(0.5)
        response = ser.read(8)  # Expected response length

        if len(response) == 8:
            print(f"Successfully changed sensor {current_id} → {new_id}")
        else:
            print("Failed to change sensor address.")
        
        ser.close()
    except serial.SerialException as e:
        print(f"Serial error: {e}")

# Change sensor 0x01 to 0x02
change_modbus_address(0x01, 0x02)
