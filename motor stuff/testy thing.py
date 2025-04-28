import RPi.GPIO as GPIO
import time

# GPIO Pin Definitions
RPWM = 18  # Right PWM input (GPIO18 - Pin 12)
LPWM = 13  # Left PWM input (GPIO13 - Pin 33)
REN = 23   # Right Enable (GPIO23 - Pin 16)
LEN = 24   # Left Enable (GPIO24 - Pin 18)

# Setup
GPIO.setmode(GPIO.BCM)      # Use BCM GPIO numbering
GPIO.setwarnings(False)     # Disable warnings

# Set all control pins as output
GPIO.setup(RPWM, GPIO.OUT)
GPIO.setup(LPWM, GPIO.OUT)
GPIO.setup(REN, GPIO.OUT)
GPIO.setup(LEN, GPIO.OUT)

# Safe startup: Set PWM pins LOW first
GPIO.output(RPWM, GPIO.LOW)
GPIO.output(LPWM, GPIO.LOW)

# Enable the BTS7960 outputs
GPIO.output(REN, GPIO.HIGH)
GPIO.output(LEN, GPIO.HIGH)

print("Starting motor test sequence...")

# === Motor Forward Test ===
print("Motor Forward")
GPIO.output(RPWM, GPIO.HIGH)
GPIO.output(LPWM, GPIO.LOW)
time.sleep(3)  # Run motor forward for 3 seconds

# === Motor Stop ===
print("Motor Stop")
GPIO.output(RPWM, GPIO.LOW)
GPIO.output(LPWM, GPIO.LOW)
time.sleep(2)  # Pause for 2 seconds

# === Motor Reverse Test ===
print("Motor Reverse")
GPIO.output(RPWM, GPIO.LOW)
GPIO.output(LPWM, GPIO.HIGH)
time.sleep(3)  # Run motor reverse for 3 seconds

# === Motor Stop ===
print("Motor Stop")
GPIO.output(RPWM, GPIO.LOW)
GPIO.output(LPWM, GPIO.LOW)
time.sleep(2)

# Cleanup
GPIO.output(REN, GPIO.LOW)
GPIO.output(LEN, GPIO.LOW)
GPIO.cleanup()

print("Test sequence complete. All pins cleaned up.")
