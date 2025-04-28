import RPi.GPIO as GPIO
import time

# Pin setup
RPWM = 18
LPWM = 23
R_EN = 24
L_EN = 25

# GPIO mode
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Setup pins
GPIO.setup(RPWM, GPIO.OUT)
GPIO.setup(LPWM, GPIO.OUT)
GPIO.setup(R_EN, GPIO.OUT)
GPIO.setup(L_EN, GPIO.OUT)

# PWM setup
pwm_r = GPIO.PWM(RPWM, 1000)  # 1 kHz frequency
pwm_l = GPIO.PWM(LPWM, 1000)

# Start PWM with 0% duty cycle
pwm_r.start(0)
pwm_l.start(0)

def motor_forward(speed):
    GPIO.output(R_EN, GPIO.HIGH)
    GPIO.output(L_EN, GPIO.HIGH)
    pwm_r.ChangeDutyCycle(speed)  # speed 0-100%
    pwm_l.ChangeDutyCycle(0)

def motor_backward(speed):
    GPIO.output(R_EN, GPIO.HIGH)
    GPIO.output(L_EN, GPIO.HIGH)
    pwm_r.ChangeDutyCycle(0)
    pwm_l.ChangeDutyCycle(speed)

def motor_stop():
    GPIO.output(R_EN, GPIO.LOW)
    GPIO.output(L_EN, GPIO.LOW)
    pwm_r.ChangeDutyCycle(0)
    pwm_l.ChangeDutyCycle(0)

try:
    while True:
        print("Forward")
        motor_forward(80)  # 80% speed
        time.sleep(2)

        print("Stop")
        motor_stop()
        time.sleep(1)

        print("Backward")
        motor_backward(80)  # 80% speed
        time.sleep(2)

        print("Stop")
        motor_stop()
        time.sleep(1)

except KeyboardInterrupt:
    print("Cleaning up GPIO")
    pwm_r.stop()
    pwm_l.stop()
    GPIO.cleanup()
