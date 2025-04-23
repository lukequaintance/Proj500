import os
import time
import threading
import serial
import lgpio
import cv2
from collections import deque
from Image_Capture import CameraThread
from sensor_module import poll_all_sensors, append_results_to_json  # rename your sensor file accordingly
from motorDriver import RockProbe, SensorProbe
from RTU_Code import driveForward
import motorDriver

# --- Configuration ---
SAVE_DIR = '/media/lukeq/Seagate Portable Drive/Images'
CAM_INDEX = 0
IMAGE_INTERVAL_SEC = 10.0

PROBE_TIME_SEC = 60.0
STEP_DISTANCE_METERS = 5.0
DIST_BETWEEN_PROBES = 0

# Serial port for soil sensors
COM_PORT = "/dev/ttyUSB1"
BAUD_RATE = 4800
SENSOR_1_ID = 0x01
SENSOR_2_ID = 0x02

# Rolling average setup for current sampling
WINDOW_SIZE     = 20

# Initialize the motor
motorDriver.setUpMotor()

# Thread control flags
global_running      = True
stop_event          = threading.Event()
print_lock          = threading.Lock()


# Rolling average setup
ROLLING_WINDOW_SIZE = 20
rolling_current = deque(maxlen=ROLLING_WINDOW_SIZE)

#vars for soil tseting and rock detection
current_when_rock = 400
current_when_full_stroke = 40
sensorTestTime = 60

def sample_current()-> float:
    
    current = motorDriver.ina.current  # Current in mA
    rolling_current.append(current)
    avg_current = sum(rolling_current) / len(rolling_current)

    return avg_current



# --- Actuator + Sensor Thread ---                                                                  #WE NEED THIS TO BE MORE SIMPLE
class ActuatorSensorThread(threading.Thread):
    def __init__(self, ser: serial.Serial):
        super().__init__()
        self._stop = threading.Event()
        self.ser  = ser
        self.curr_window = deque(maxlen=WINDOW_SIZE)

    def run(self):
            
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
                    print("thre is a rock. moving and trying again")
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
            print("probing senesor")
            motorDriver.probeMove("forward")
            time.sleep(30)
            time.sleep(sensorTestTime)
            #read sensor 
            print("moving sensor probe backwards")
            motorDriver.probeMove("backward")
            time.sleep(30)
            # continue with the code

    def stop(self):
        self._stop.set()

# --- Main Execution ---
if __name__ == "__main__":
    # Open serial port
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    print(f"Serial {COM_PORT} @ {BAUD_RATE}")

    # Start camera capture
    cam_thread = CameraThread(CAM_INDEX, SAVE_DIR, IMAGE_INTERVAL_SEC)
    cam_thread.start()

    # Start actuation + sensor thread
    act_thread = ActuatorSensorThread(ser)
    act_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[Main] Shutting down...")
        global_running = False
        stop_event.set()
        cam_thread.stop(); cam_thread.join()
        act_thread.stop(); act_thread.join()
        ser.close()
        lgpio.close()
        print("[Main] Shutdown complete.")
