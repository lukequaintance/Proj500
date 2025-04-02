import lgpio
import time
import board
import busio
import motorDriver
import sys
import termios
import tty

# Initialize the motor
motorDriver.setUpMotor()

def get_key():
    """Reads a single key press from the user without needing Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

print("Use 'w' to move forward, 's' to move backward, and 'q' to quit.")

while True:
    key = get_key()
    
    if key == 'w':
        #print("Motor Forward")
        motorDriver.probeMove("forward")
        motorDriver.testMove("forward")
    elif key == 's':
        #print("Motor Backward")
        motorDriver.probeMove("backward")
        motorDriver.testMove("backward")
    elif key == 'q':
        print("Exiting...")
        break
    
    # Read and display sensor values
    bus_voltage = motorDriver.ina.bus_voltage      # Voltage in V
    shunt_voltage = motorDriver.ina.shunt_voltage  # Voltage drop across shunt resistor in V
    current = motorDriver.ina.current              # Current in mA
    power = motorDriver.ina.power                  # Power in mW
    
    load_output = motorDriver.loadOnMotor(current)
    print(f"Load: {load_output:.2f}")
    
    time.sleep(0.1)
