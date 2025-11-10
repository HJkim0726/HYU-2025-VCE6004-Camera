import PySpin
import cv2
import numpy as np


def debug_pixel_format(cam):
    """
    Print current PixelFormat of the camera.

    Args:
        cam (PySpin.CameraPtr): Initialized camera object.
    """
    nodemap = cam.GetNodeMap()
    pixel_format_enum = PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat"))

    if not PySpin.IsReadable(pixel_format_enum):
        print("[WARN] PixelFormat is not readable.")
        return

    current_entry = pixel_format_enum.GetCurrentEntry()
    if not PySpin.IsReadable(current_entry):
        print("[WARN] Current PixelFormat entry is not readable.")
        return

    symbolic = current_entry.GetSymbolic()
    print(f"[INFO] Current PixelFormat: {symbolic}")


def set_pixel_format(cam):
    """
    Set camera PixelFormat to a readable color format.

    Args:
        cam (PySpin.CameraPtr): Initialized camera object.
    """
    nodemap = cam.GetNodeMap()
    pixel_format_enum = PySpin.CEnumerationPtr(nodemap.GetNode("PixelFormat"))
    if not PySpin.IsWritable(pixel_format_enum):
        print("[WARN] Cannot write PixelFormat. Using current format.")
        return

    # Try to use a good color format if available.
    # Order of preference: RGB8Packed → BGR8 → Mono8
    for fmt_name in ["RGB8Packed", "BGR8", "Mono8"]:
        entry = pixel_format_enum.GetEntryByName(fmt_name)
        if PySpin.IsReadable(entry):
            pixel_format_enum.SetIntValue(entry.GetValue())
            print(f"[INFO] PixelFormat set to {fmt_name}")
            return

    print("[WARN] No preferred PixelFormat found. Using default.")


def convert_image_to_bgr(image_result: PySpin.ImagePtr) -> np.ndarray:
    """
    Convert a PySpin image to an OpenCV BGR image.

    Args:
        image_result (PySpin.ImagePtr): Captured image from FLIR camera.

    Returns:
        frame_bgr (np.ndarray): BGR image ready for OpenCV.
    """
    img = image_result.GetNDArray()
    pixel_format = image_result.GetPixelFormat()

    # Try to get symbolic pixel format name (e.g. "RGB8", "BayerRG8", ...)
    fmt_name = None
    try:
        fmt_name = image_result.GetPixelFormatName()
    except AttributeError:
        pass

    if fmt_name is not None:
        fmt_name_upper = fmt_name.upper()
        # Uncomment once if you want to inspect:
        # print(f"[DEBUG] PixelFormat name: {fmt_name}, enum value: {pixel_format}")

        # --- Mono formats ---
        if "MONO8" in fmt_name_upper:
            frame_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

        # --- RGB formats (your camera: "RGB8") ---
        elif "RGB8" in fmt_name_upper:
            # Image is in RGB order -> convert to BGR for OpenCV
            frame_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

        # --- BGR formats ---
        elif "BGR8" in fmt_name_upper:
            frame_bgr = img

        # --- Bayer formats ---
        elif "BAYERRG8" in fmt_name_upper:
            frame_bgr = cv2.cvtColor(img, cv2.COLOR_BAYER_RG2BGR)
        elif "BAYERGB8" in fmt_name_upper:
            frame_bgr = cv2.cvtColor(img, cv2.COLOR_BAYER_GB2BGR)
        elif "BAYERGR8" in fmt_name_upper:
            frame_bgr = cv2.cvtColor(img, cv2.COLOR_BAYER_GR2BGR)
        elif "BAYERBG8" in fmt_name_upper:
            frame_bgr = cv2.cvtColor(img, cv2.COLOR_BAYER_BG2BGR)

        # --- Unknown but named format ---
        else:
            print(f"[WARN] Unhandled PixelFormat name '{fmt_name}'. Using generic conversion.")
            if img.ndim == 2:
                frame_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            else:
                frame_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    else:
        # No name API, fallback by shape
        print(f"[WARN] PixelFormat ({pixel_format}) without name. Using generic conversion.")
        if img.ndim == 2:
            frame_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        else:
            frame_bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    return frame_bgr



def acquire_single_frame(cam, timeout_ms=1000):
    """
    Acquire a single frame from the camera.

    Args:
        cam (PySpin.CameraPtr): Initialized camera object.
        timeout_ms (int): Timeout in milliseconds for image capture.

    Returns:
        frame_bgr (np.ndarray | None): Captured BGR frame or None if failed.
    """
    nodemap = cam.GetNodeMap()

    # Set acquisition mode to SingleFrame
    acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode("AcquisitionMode"))
    if not PySpin.IsWritable(acquisition_mode):
        print("[ERROR] Cannot set AcquisitionMode.")
        return None

    single_entry = acquisition_mode.GetEntryByName("SingleFrame")
    acquisition_mode.SetIntValue(single_entry.GetValue())

    # Start capturing
    cam.BeginAcquisition()
    try:
        image_result = cam.GetNextImage(timeout_ms)
        if image_result.IsIncomplete():
            print(f"[WARN] Image incomplete. Status: {image_result.GetImageStatus()}")
            image_result.Release()
            return None

        frame = convert_image_to_bgr(image_result)
        image_result.Release()
        return frame

    finally:
        cam.EndAcquisition()


def lab2_single_frame(output_path="single_frame.png"):
    """
    Capture one frame from the FLIR camera and save it to disk.

    Args:
        output_path (str): Path to save the captured frame.
    """
    # Step 1. Initialize Spinnaker system
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()

    if cam_list.GetSize() == 0:
        print("[ERROR] No FLIR cameras found.")
        cam_list.Clear()
        system.ReleaseInstance()
        return

    cam = cam_list[0]

    try:
        # Step 2. Initialize camera
        cam.Init()

        # Step 3. Check & set PixelFormat
        print("[INFO] Before setting PixelFormat:")
        debug_pixel_format(cam)

        set_pixel_format(cam)

        print("[INFO] After setting PixelFormat:")
        debug_pixel_format(cam)

        # Step 4. Capture one frame
        frame = acquire_single_frame(cam)
        if frame is None:
            print("[ERROR] Failed to acquire single frame.")
            return

        # Step 5. Save file only (no GUI)
        cv2.imwrite(output_path, frame)
        print(f"[INFO] Saved single frame to: {output_path}")

    finally:
        # Step 6. Cleanup resources
        cam.DeInit()
        del cam
        cam_list.Clear()
        system.ReleaseInstance()


if __name__ == "__main__":
    lab2_single_frame()
