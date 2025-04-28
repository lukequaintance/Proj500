from gpiozero import PWMOutputDevice, DigitalOutputDevice
from time import sleep

# Define GPIO pins
RPWM_pin = 18
LPWM_pin = 19
REN_pin = 23  # optional, any free GPIO
LEN_pin = 24  # optional, any free GPIO

# Setup motor driver pins
RPWM = PWMOutputDevice(RPWM_pin)
LPWM = PWMOutputDevice(LPWM_pin)
REN = DigitalOutputDevice(REN_pin)
LEN = DigitalOutputDevice(LEN_pin)

# Enable motor driver
REN.on()
LEN.on()

while True:
    # Motor forward
    print("Motor forward")
    RPWM.value = 0.7  # 70% speed
    LPWM.value = 0
    sleep(2)

    # Motor backward
    print("Motor backward")
    RPWM.value = 0
    LPWM.value = 0.7  # 70% speed
    sleep(2)
