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

# Initialize the motor
motorDriver.setUpMotor()

# Rolling average setup
ROLLING_WINDOW_SIZE = 20
rolling_current = deque(maxlen=ROLLING_WINDOW_SIZE)

# Shared variable to safely stop the thread
running = True

# Lock for clean print statements
print_lock = threading.Lock()

# create a stop thread even 
stop_event = threading.Event()

def get_key():
    """Reads a single key press from the user without needing Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def sample_current():
    """Background thread to sample current and print rolling average every 1 sec."""
    while running:
        current = motorDriver.ina.current  # Current in mA
        rolling_current.append(current)
        avg_current = sum(rolling_current) / len(rolling_current)

        load_output = motorDriver.loadOnMotor(avg_current)
        currentMass = load_output * 0.1019716213

        with print_lock:
            print("\033[2K\r", end="")  # Clear current line
            print(f"\n[500ms Sample]")
            print(f"Current:      {current:.2f} mA")
            print(f"Rolling Avg:  {avg_current:.2f} mA")
            print(f"Load:         {load_output:.2f}")
            print(f"Mass:         {currentMass:.2f} kg\n")

            if avg_current < 0.15:  # the current when the actuator has reached full stroke
                stop_event.set() 
            
            elif avg_current > 0.35:    #if there is a rock the device has to move
                print("there is a rock, retracting and moving") 

            else: # carry on getting the current till an even happens 
                time.sleep(1.0)


# Start the current sampling thread


print("Use 'w' to move forward, 's' to move backward, and 'q' to quit.")

# Main loop
while True:
    key = get_key()
    
    with print_lock:
        if key == 'w':
            motorDriver.probeMove("forward")
            motorDriver.testMove("forward")
            print("Moving forward...")
            time.sleep(2) # this will sleep the timer so the current can stabalise
            thread = threading.Thread(target=sample_current, daemon=True)
            thread.start() # this starts the thread to samples the current 

        elif key == 's':
            motorDriver.probeMove("backward")
            motorDriver.testMove("backward")
            print("Moving backward...")
            time.sleep(2) # this will sleep the timer so the current can stabalise
            thread = threading.Thread(target=sample_current, daemon=True)
            thread.start()

        elif key == 'q':
            print("Exiting...")
            running = False
            thread.join()
            break
