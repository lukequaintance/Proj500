import lgpio
import time

# Open GPIO chip
h = lgpio.gpiochip_open(0)

# Pin Definitions (BCM numbering)
RPWM = 18  # Right PWM input
LPWM = 13  # Left PWM input
REN = 23   # Right Enable
LEN = 24   # Left Enable

# Setup all pins as OUTPUT, initial LOW
for pin in (RPWM, LPWM, REN, LEN):
    lgpio.gpio_claim_output(h, pin, 0)

# Safe startup
lgpio.gpio_write(h, RPWM, 0)
lgpio.gpio_write(h, LPWM, 0)

# Enable H-bridge outputs
lgpio.gpio_write(h, REN, 1)
lgpio.gpio_write(h, LEN, 1)

print("Starting motor test sequence...")

# === Motor Forward Test ===
print("Motor Forward")
lgpio.gpio_write(h, RPWM, 1)
lgpio.gpio_write(h, LPWM, 0)
time.sleep(3)

# === Motor Stop ===
print("Motor Stop")
lgpio.gpio_write(h, RPWM, 0)
lgpio.gpio_write(h, LPWM, 0)
time.sleep(2)

# === Motor Reverse Test ===
print("Motor Reverse")
lgpio.gpio_write(h, RPWM, 0)
lgpio.gpio_write(h, LPWM, 1)
time.sleep(3)

# === Motor Stop ===
print("Motor Stop")
lgpio.gpio_write(h, RPWM, 0)
lgpio.gpio_write(h, LPWM, 0)
time.sleep(2)

# Disable H-bridge
lgpio.gpio_write(h, REN, 0)
lgpio.gpio_write(h, LEN, 0)

# Cleanup
lgpio.gpiochip_close(h)

print("Test sequence complete. All pins cleaned up.")
