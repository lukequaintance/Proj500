import time
import board
import busio
import motorDriver
import sys
import termios
import tty
from collections import deque
import threading
import serial
import json
import atexit
from sensor_module import poll_all_sensors, append_results_to_json
from Image_Capture import CameraThread
# COM Port Configuration
COM_PORT = "/dev/ttyUSB0"
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

# Initialize the motor
motorDriver.setUpMotor()
motorDriver.testMove("backward")
motorDriver.probeMove("backward")
time.sleep(30)


# Rolling average setup
ROLLING_WINDOW_SIZE = 20
rolling_current = deque(maxlen=ROLLING_WINDOW_SIZE)


#vars for soil tseting and rock detection
current_when_rock = 400
current_when_full_stroke = 40
sensorTestTime = 60

# Shared variable to safely stop the thread
running = True

# Lock for clean print statements
print_lock = threading.Lock()

# create a stop thread even 
stop_event = threading.Event()


#DEBUGGING
#def get_key():
#    """Reads a single key press from the user without needing Enter."""
#    fd = sys.stdin.fileno()
#    old_settings = termios.tcgetattr(fd)
#    try:
#        tty.setraw(fd)
#        ch = sys.stdin.read(1)
#    finally:
#        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
#    return ch

def sample_current()-> float:
    
    current = motorDriver.ina.current  # Current in mA
    rolling_current.append(current)
    avg_current = sum(rolling_current) / len(rolling_current)

    return avg_current

def camera_shutdown():
    print("[CLEANUP] Stopping camera thread...")
    camera_thread.stop()
    print("[CLEANUP] Camera thread stopped.")

atexit.register(camera_shutdown)

print("Here 1")
#Initialise Save File
SAVE_DIR = '/media/soil/Seagate Portable Drive/Images'
camera_thread = CameraThread(camera_index = 0, save_dir = SAVE_DIR, interval = 6000.0)

print("Here 2")

#Initialise Camera
print("[INIT] Starting camera thread")
camera_thread.start()
print("Here 3")
#Initialise Serial Port
ser = None
print("Here 4")

#print("Use 'w' to move forward, 's' to move backward, and 'q' to quit.")

# Main loop
try:
    while True:
        try:
            
            print("[STEP] Opening serial connection...")
            ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
            print("[OK] Serial connection opened.")

            print("[STEP] Moving forward for rock testing...")
            motorDriver.testMove("forward")

            # Start stroke timer
            start_time = time.perf_counter()
            elapsed = 0.0
            rolling_current.clear()
            print("[STEP] Checking for rocks...")
            time.sleep(2)

            while elapsed < 35:
                avg_current = sample_current()
                current_time = time.perf_counter()
                elapsed = current_time - start_time

                print(f"[INFO] Avg current: {avg_current:.2f} mA | Time elapsed: {elapsed:.1f}s")

                if avg_current > current_when_rock:
                    print("[ALERT] Rock detected! Moving backward and retrying...")
                    motorDriver.testMove("backward")
                    time.sleep(40)
                    #Move RTU to new position

                    print("[STEP] Trying new position...")
                    motorDriver.testMove("forward")
                    time.sleep(1)

                    # Reset timer and current window
                    start_time = time.perf_counter()
                    elapsed = 0.0
                    rolling_current.clear()

            print("[OK] No rocks detected. Proceeding with soil probe...")

            motorDriver.testMove("backward")
            time.sleep(20)

            print("[STEP] Probing soil...")
            motorDriver.probeMove("forward")
            time.sleep(30 + sensorTestTime)

            # Sensor reading
            print("[STEP] Reading sensor data...")
            print("\nSensor 1 Data:")
            sensor1_data = poll_all_sensors(ser, SENSOR_1_ID)
            for label, value in sensor1_data.items():
                print(f"  {label}: {value}")

            print("\nSensor 2 Data:")
            sensor2_data = poll_all_sensors(ser, SENSOR_2_ID)
            for label, value in sensor2_data.items():
                print(f"  {label}: {value}")

            print("[STEP] Saving sensor data...")
            append_results_to_json(sensor1_data, sensor2_data)
            print("[OK] Sensor data saved to JSON.")

            print("[STEP] Retracting sensor and moving backward...")
            motorDriver.probeMove("backward")
            motorDriver.testMove("backward")
            time.sleep(30)

            #Move RTU to new Position

        except serial.SerialException as e:
            print(f"[ERROR] Serial port error: {e}")
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")

except KeyboardInterrupt:
    print("[Exit] Interrupted by user")

finally:
    print("[CLEANUP] Releasing resources...")
    if ser:
        ser.close()
        print("[CLEANUP] Serial port closed.")
    
    camera_shutdown()
    print("[CLEANUP] Camera released.")

            



      
