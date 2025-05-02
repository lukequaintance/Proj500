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
import csv
import matplotlib.pyplot as plt
import pandas as pd

# Initialize the motor
motorDriver.setUpMotor()

# Rolling average setup
ROLLING_WINDOW_SIZE = 20
rolling_current = deque(maxlen=ROLLING_WINDOW_SIZE)


#vars for soil tseting and rock detection
current_when_rock = 300
current_when_full_stroke = 40
sensorTestTime = 60

def log_current_to_file(elapsed_time, raw_current, current_value, filename="current_log.csv"):
    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([elapsed_time, raw_current, current_value])

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
            
            time.sleep(2) # wait for the current to stabalise            

            while elapsed < 75:
                avg_current = sample_current()
                last_action_time = start_time # sample the timer 
                current_time = time.perf_counter()
                elapsed = current_time - start_time 
                log_current_to_file(elapsed, motorDriver.ina.current, avg_current)
                print(avg_current)
                print(elapsed)


            # Load data
            df = pd.read_csv("current_log.csv")

            # Plot average current
            plt.figure()
            plt.plot(df["Elapsed Time (s)"], df["Processed Current (A)"], label="Avg Current", linewidth=2)

            # Optionally plot raw current
            if "Raw Current Value" in df.columns:
                plt.plot(df["Elapsed Time (s)"], df["Raw Current Value"], label="Raw Current", linestyle='--')

                plt.xlabel("Elapsed Time (s)")
                plt.ylabel("Current")
                plt.title("Current vs Time")
                plt.legend()
                plt.grid(True)
                plt.tight_layout()
                plt.savefig("current_plot.png")  # Save to file
                plt.show()  # Show the plot if GUI is available


                
            
            motorDriver.probeMove("backward")
            #stime.sleep(30)
            # move RTU
            
            # continue with the code

            



        elif key == 's':
            motorDriver.probeMove("backward")
            motorDriver.testMove("backward")
            print("Moving backward...")
    

        elif key == 'q':
            print("Exiting...")
            running = False
            break
