import lgpio
import time
import board
import busio
from adafruit_ina219 import INA219



def setUpMotor():
    # Initialize I2C

    global h
    global testRPWM 
    global testLPWM 
    global testREN 
    global testLEN 
    global probeRPWM 
    global probeLPWM 
    global probeREN 
    global probeLEN 
    global ina 

    i2c_bus = busio.I2C(board.SCL, board.SDA)

    # Create INA219 instance
    ina = INA219(i2c_bus)

    # Define GPIO pins
    testRPWM = 18  # Right PWM (speed control)
    testLPWM = 19  # Left PWM (speed control)
    testREN = 23   # Right Enable
    testLEN = 24   # Left Enable

    probeRPWM = 20  # Right PWM (speed control)
    probeLPWM = 21  # Left PWM (speed control)
    probeREN = 25   # Right Enable
    probeLEN = 26   # Left Enable

    # Open GPIO chip
    h = lgpio.gpiochip_open(0)

    # Setup pins as output
    for pin in [testRPWM, testLPWM, testREN, testLEN, probeRPWM, probeLPWM, probeREN, probeLEN]:
        lgpio.gpio_claim_output(h, pin)

    # Enable both sides
    lgpio.gpio_write(h, testREN, 1)
    lgpio.gpio_write(h, testLEN, 1)
    lgpio.gpio_write(h, probeREN, 1)
    lgpio.gpio_write(h, probeLEN, 1)

    
def probeMove(direction):
    if direction == "forward":
        # print("Probe actuator moving forward")
        lgpio.tx_pwm(h, probeRPWM, 1000, 100.0)  # Full power
        lgpio.tx_pwm(h, probeLPWM, 1000, 0.0)  # Off
    elif direction == "backward":
        #print("Probe actuator moving backward")
        lgpio.tx_pwm(h, probeRPWM, 1000, 0.0)  # Off
        lgpio.tx_pwm(h, probeLPWM, 1000, 100.0)  # Full power
    elif direction == "stop":
        #print("Stopping probe actuator")
        lgpio.tx_pwm(h, probeRPWM, 1000, 0.0)
        lgpio.tx_pwm(h, probeLPWM, 1000, 0.0)
    else:
        #print("Invalid argument. Use 'forward' or 'backward'.")
        lgpio.tx_pwm(h, probeRPWM, 1000, 0.0)
        lgpio.tx_pwm(h, probeLPWM, 1000, 0.0)

def testMove(direction):
    if direction == "forward":
        #print("Test actuator moving forward")
        lgpio.tx_pwm(h, testRPWM, 1000, 100.0)  # Full power
        lgpio.tx_pwm(h, testLPWM, 1000, 0.0)  # Off
    elif direction == "backward":
        #print("Test actuator moving backward")
        lgpio.tx_pwm(h, testRPWM, 1000, 0.0)  # Off
        lgpio.tx_pwm(h, testLPWM, 1000, 100.0)  # Full power
    elif direction == "stop":
        #print("Stopping test actuator")
        lgpio.tx_pwm(h, testRPWM, 1000, 0.0)
        lgpio.tx_pwm(h, testLPWM, 1000, 0.0)
    else:
        #print("Invalid argument. Use 'forward' or 'backward'.")
        lgpio.tx_pwm(h, testRPWM, 1000, 0.0)
        lgpio.tx_pwm(h, testLPWM, 1000, 0.0)

def loadOnMotor(currentIn: float) -> float:

    currentIn = currentIn / 1000  # Convert mA to A
    print(f"Current: {currentIn:.2f} A")
    load = (currentIn - 0.6104688051681327) / 0.000732893285815865

    return load



    



