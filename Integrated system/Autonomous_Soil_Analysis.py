import lgpio
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
import time
import json
from sensor_module import poll_all_sensors, append_results_to_json
from Image_Capture import init_camera, ensure_save_dir, capture_and_save, release_camera
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

#Initialise Save File
SAVE_DIR = '/media/soil/Seagate Portable Drive/Images'
ensure_save_dir(SAVE_DIR)

#Initialise Camera
cap = init_camera()




#print("Use 'w' to move forward, 's' to move backward, and 'q' to quit.")

# Main loop
while True:
    try:
        path = capture_and_save(cap, SAVE_DIR)
        print(f"Saved image to {path}")
        time.sleep(2)
        ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {COM_PORT} at {BAUD_RATE} baud.")
        motorDriver.testMove("forward")
                
        start_time = time.perf_counter() #start a timer for the stroke length
        last_action_time = start_time # sample the timer 
        current_time = time.perf_counter()
        elapsed = current_time - start_time 
                
        print("testing for rocks")
        time.sleep(2) # wait for the current to stabalise            

        while elapsed < 35:
            avg_current = sample_current()
            last_action_time = start_time # sample the timer 
            current_time = time.perf_counter()
            elapsed = current_time - start_time 
            print(avg_current)
            print(elapsed)

            if avg_current > current_when_rock:
                motorDriver.testMove("backward")
                print("there is a rock. moving and trying again")
                time.sleep(40) # wait for 40 second in case the it was at full stroke 
                # move buggy to new location 
                motorDriver.testMove("forward")
                print("moving forwards")    
                time.sleep(1)
                #reset the timer back to 0
                start_time = time.perf_counter()
                last_action_time = start_time
                elapsed = 0.0
                rolling_current.clear() # clear the average so the spike does not interrupt the reading
                
        print("this ground is soft enough, moving soil sensor for testing")
        motorDriver.testMove("backward")
        time.sleep(20)
        # move RTU
        print("probing sensor")
        motorDriver.probeMove("forward")
        time.sleep(30)
        time.sleep(sensorTestTime)
        
        #read sensor
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

        print("moving sensor probe backwards")
        motorDriver.probeMove("backward")
        motorDriver.testMove("backward")
        time.sleep(30)
        # continue with the code


    except serial.SerialException as e:
        print(f"Serial port error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if ser:
            ser.close()
            print("Serial port closed.")
            release_camera(cap)

            



      
