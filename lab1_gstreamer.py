import cv2
import os

# NOTE: The print_camera_info function is not applicable to GStreamer/OpenCV
# as it relies on PySpin's hardware node access. We will print OS device info instead.

def print_gstreamer_info(device_path):
    """
    Attempts to print basic info about a video device path.
    """
    print("=== Video Device Information ===")
    print(f"  Device Path: {device_path}")
    
    # Try to read the device link (e.g., to see what it links to)
    try:
        real_path = os.path.realpath(device_path)
        print(f"  Real Path  : {real_path}")
    except OSError:
        print("  Real Path  : Could not resolve link")


def lab1_gstreamer_info():
    """
    Finds and attempts to initialize the first available video device using GStreamer/OpenCV.
    """
    video_devices = sorted([dev for dev in os.listdir("/dev") if dev.startswith("video")])

    num_devices = len(video_devices)
    print(f"[INFO] Number of V4L2 video devices detected: {num_devices}")

    if num_devices == 0:
        print("[INFO] No /dev/video* devices found.")
        return

    # Use the first detected device
    device_name = video_devices[0]
    device_path = f"/dev/{device_name}"
    
    print_gstreamer_info(device_path)

    try:
        # 1) Construct a basic GStreamer pipeline for V4L2
        # This pipeline attempts to open the device and convert to a format OpenCV can use.
        # NOTE: If using the Jetson's onboard CSI camera, you would use 'nvarguscamerasrc'.
        # For a standard USB camera (V4L2), the default OpenCV backend is often sufficient.
        
        # A simple V4L2 pipeline string for testing the device:
        # f'v4l2src device={device_path} ! video/x-raw, width=640, height=480 ! videoconvert ! appsink'
        
        cap = cv2.VideoCapture(device_path, cv2.CAP_V4L2)
        
        # If the camera is the Jetson's CSI camera, use this (adjust width/height/framerate):
        # gstreamer_pipeline = (
        #     f'nvarguscamerasrc sensor_id=0 ! '
        #     'video/x-raw(memory:NVMM), width=1280, height=720, framerate=30/1 ! '
        #     'nvvidconv ! video/x-raw, format=BGRx ! '
        #     'videoconvert ! video/x-raw, format=BGR ! appsink'
        # )
        # cap = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)

        if cap.isOpened():
            print(f"[SUCCESS] Successfully opened {device_path} using OpenCV/V4L2.")
            # Reading a frame proves the pipeline works
            ret, frame = cap.read()
            if ret:
                print(f"[SUCCESS] Read one frame of size: {frame.shape}")
            else:
                print("[WARNING] Could not read frame from device.")
        else:
            print(f"[ERROR] Failed to open {device_path}. The device might be in use or requires a specific GStreamer pipeline (e.g., for CSI).")

    finally:
        # 2) Proper cleanup
        if 'cap' in locals() and cap.isOpened():
            cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    # Ensure OpenCV is installed with GStreamer support on your Jetson
    # Use 'import cv2' to verify.
    lab1_gstreamer_info()