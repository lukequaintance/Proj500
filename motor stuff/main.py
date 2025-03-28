import lgpio
import time
import board
import busio
from adafruit_ina219 import INA219
import motorDriver

#this inits the pins for all the stuff associated with the motor 
motorDriver.setUpMotor()





while True:
    print("Motor Forward")
    motorDriver.probeMove("forward")
    motorDriver.testMove("forward")
    time.sleep(0)
    # Read values
    bus_voltage = motorDriver.ina.bus_voltage      # Voltage in V
    shunt_voltage = motorDriver.ina.shunt_voltage  # Voltage drop across shunt resistor in V
    current = motorDriver.ina.current              # Current in mA
    power = motorDriver.ina.power                  # Power in mW
    # Print results
    #print(f"Bus Voltage: {bus_voltage:.2f} V")
    #print(f"Shunt Voltage: {shunt_voltage:.5f} V")
    #print(f"Current: {current:.2f} mA")
    #print(f"Power: {power:.2f} mW")
    load_output = motorDriver.loadOnMotor(current)
    print(f"Load: {load_output:.2f}")

    print("Motor Backward")
    motorDriver.probeMove("backward")
    motorDriver.testMove("backward")
    time.sleep(0)
    # Read values
    bus_voltage = motorDriver.ina.bus_voltage      # Voltage in V
    shunt_voltage = motorDriver.ina.shunt_voltage  # Voltage drop across shunt resistor in V
    current = motorDriver.ina.current              # Current in mA
    power = motorDriver.ina.power                  # Power in mW
    # Print results
    #print(f"Bus Voltage: {bus_voltage:.2f} V")
    #print(f"Shunt Voltage: {shunt_voltage:.5f} V")
    #print(f"Current: {current:.2f} mA")
    #print(f"Power: {power:.2f} mW")
    #load_output = loadOnMotor(current)
    #print(f"Load: {load_output:.2f}")
