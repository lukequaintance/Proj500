import cv2
import time
import os


def init_camera(camera_index: int = 0) -> cv2.VideoCapture:
    """
    Initialize and return the OpenCV VideoCapture object.
    Raises RuntimeError if the camera cannot be opened.
    """
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open camera at index {camera_index}")
    return cap


def ensure_save_dir(save_dir: str) -> None:
    """
    Create the directory (and parents) if it doesn't exist.
    """
    os.makedirs(save_dir, exist_ok=True)


def capture_and_save(cap: cv2.VideoCapture, save_dir: str) -> str:
    """
    Capture one frame from the camera and save it to save_dir.
    Returns the full path of the saved image.
    Raises RuntimeError on capture failure.
    """
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Failed to capture image from camera.")

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"capture_{timestamp}.jpg"
    filepath = os.path.join(save_dir, filename)
    cv2.imwrite(filepath, frame)
    return filepath


def release_camera(cap: cv2.VideoCapture) -> None:
    """
    Release the VideoCapture and destroy any OpenCV windows.
    """
    cap.release()
    cv2.destroyAllWindows()

#Initialise Save File
SAVE_DIR = '/media/lukeq/Seagate Portable Drive/Images'
ensure_save_dir(SAVE_DIR)

#Initialise Camera
cap = init_camera()

try:
    while True:
        path = capture_and_save(cap, SAVE_DIR)
        print(f"Saved image to {path}")
        time.sleep(2)
except KeyboardInterrupt:
    print("Interrupted by user.")
finally:
    release_camera(cap)