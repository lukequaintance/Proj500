import os
import time
import serial
import json
import sys
import termios
import tty
from collections import deque
import threading
import board
import busio
#import lgpio
import cv2
from Image_Capture import init_camera, ensure_save_dir, capture_and_save, release_camera
import sensor_json_write
import motorDriver
import RTU_Code

#Initialise Save File
SAVE_DIR = '/media/lukeq/Seagate Portable Drive/Images'
ensure_save_dir(SAVE_DIR)

#Initialise Sensor Values
#COM Port Configuration
COM_PORT = "/dev/ttyUSB0"
BAUD_RATE = 4800

# Sensor Device Addresses
SENSOR_1_ID = 0x01  # First sensor address
SENSOR_2_ID = 0x02  # Second sensor address

# Sensor Data Addresses
MOIST = 0x00
TEMP = 0x01
COND = 0x02
PH = 0x03
N = 0x04
P = 0x05
K = 0x06

DATA_CODES = [MOIST, TEMP, COND, PH, N, P, K]

#Initialise Motor
motorDriver.setUpMotor()

#Initialise Camera
cap = init_camera()


