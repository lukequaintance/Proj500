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


# Thread control flags
global_running      = True
stop_event          = threading.Event()
print_lock          = threading.Lock()

# --- Current sampling thread ---
def sample_current_for_rock(rolling_current: deque):                                                         #NEED TO CHANGE THIS
    from motorDriver import ina
    rolling_current.clear()
    while global_running:
        current = ina.current
        rolling_current.append(current)
        avg_current = sum(rolling_current) / len(rolling_current)
        with print_lock:
            print(f"[Current] {current:.2f} mA | Avg {avg_current:.2f} mA")
        if avg_current < 0.15 or avg_current > 0.35:
            stop_event.set()
            break
        time.sleep(1.0)

# --- Actuator + Sensor Thread ---                                                                  #WE NEED THIS TO BE MORE SIMPLE
class ActuatorSensorThread(threading.Thread):
    def __init__(self, ser: serial.Serial):
        super().__init__()
        self._stop = threading.Event()
        self.ser  = ser
        self.curr_window = deque(maxlen=WINDOW_SIZE)

    def run(self):
        global global_running
        while not self._stop.is_set():
            # 1. Rock probe with current monitor
            print("[Actuator] Starting rock probe...")
            stop_event.clear()
            self.curr_window.clear()
            rock_thread = threading.Thread(target=sample_current_for_rock,
                                           args=(self.curr_window,))
            rock_thread.start()
            RockProbe("forward")
            # Wait until stop_event: either full stroke or rock hit
            while not stop_event.is_set():
                time.sleep(0.01)
            RockProbe("stop")
            rock_thread.join()

            # Decide based on current
            if any(val > 0.35 for val in self.curr_window):
                print("[Actuator] Rock detected, skipping this point.")
                driveForward(STEP_DISTANCE_METERS)
                continue
            else:
                print("[Actuator] No rock, proceeding to sensor probe.")

            # 2. Sensor actuator probe (no current monitoring)
            print(f"[Actuator] Probing sensors for {PROBE_TIME_SEC}s...")
            SensorProbe("forward")
            time.sleep(PROBE_TIME_SEC)
            SensorProbe("stop")

            # 3. Poll soil sensors
            print("[Sensors] Polling soil sensors...")
            s1 = poll_all_sensors(self.ser, SENSOR_1_ID)
            s2 = poll_all_sensors(self.ser, SENSOR_2_ID)
            append_results_to_json(s1, s2)
            print("[Sensors] Data saved to JSON.")

            # 4. Advance to next location
            print(f"[Actuator] Moving forward {STEP_DISTANCE_METERS}m...")
            driveForward(STEP_DISTANCE_METERS)

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
