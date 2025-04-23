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

def sample_current()-> float:
    
    current = motorDriver.ina.current  # Current in mA
    rolling_current.append(current)
    avg_current = sum(rolling_current) / len(rolling_current)

    return avg_current




print("Use 'w' to move forward, 's' to move backward, and 'q' to quit.")

# Main loop
while True:
    key = get_key()
    
    with print_lock:
        if key == 'w':
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

            



        elif key == 's':
            motorDriver.probeMove("backward")
            motorDriver.testMove("backward")
            print("Moving backward...")
    

        elif key == 'q':
            print("Exiting...")
            running = False
            break
