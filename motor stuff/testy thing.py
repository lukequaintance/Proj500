import RPi.GPIO as GPIO
import time

# Define pins
RPWM = 18  # GPIO18 (Pin 12)
LPWM = 13  # GPIO13 (Pin 33)
REN = 23   # GPIO23 (Pin 16)
LEN = 24   # GPIO24 (Pin 18)

GPIO.setmode(GPIO.BCM)
GPIO.setup(RPWM, GPIO.OUT)
GPIO.setup(LPWM, GPIO.OUT)
GPIO.setup(REN, GPIO.OUT)
GPIO.setup(LEN, GPIO.OUT)

# Create PWM objects
pwm_r = GPIO.PWM(RPWM, 1000)  # 1kHz frequency
pwm_l = GPIO.PWM(LPWM, 1000)

# Enable the driver
GPIO.output(REN, GPIO.HIGH)
GPIO.output(LEN, GPIO.HIGH)

# Test: Motor Forward
pwm_l.start(0)   # LPWM 0%
pwm_r.start(50)  # RPWM 50%

time.sleep(2)

# Test: Motor Reverse
pwm_r.ChangeDutyCycle(0)
pwm_l.ChangeDutyCycle(50)

time.sleep(2)

# Stop motor
pwm_r.ChangeDutyCycle(0)
pwm_l.ChangeDutyCycle(0)

pwm_r.stop()
pwm_l.stop()
GPIO.cleanup()
