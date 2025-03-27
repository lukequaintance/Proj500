import cv2
import time
import os

# Set the mount point for your external drive
save_dir = "/media/lukeq/Seagate Portable Drive/Images"
os.makedirs(save_dir, exist_ok=True)

# Initialize the USB camera (change the index if needed)
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

try:
    while True:
        ret, frame = cap.read()
        if ret:
            # Create a timestamped filename
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = os.path.join(save_dir, f"capture_{timestamp}.jpg")
            # Save the image to the external drive
            cv2.imwrite(filename, frame)
            print(f"Saved image {filename}")
        else:
            print("Failed to capture image.")

        # Wait for 60 seconds before capturing next image
        time.sleep(10)

except KeyboardInterrupt:
    print("Program interrupted by user.")

finally:
    cap.release()
    cv2.destroyAllWindows()
