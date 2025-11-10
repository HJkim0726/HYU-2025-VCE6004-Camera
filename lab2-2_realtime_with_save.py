import os
import time
import PySpin
import cv2
import numpy as np


def debug_pixel_format(cam):
    """
    Print current PixelFormat of the camera.

    Args:
        cam (PySpin.CameraPtr): Initialized camera object.

    Returns:
        None
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

    Returns:
        None
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




def configure_camera_resolution_fps(cam, width=1280, height=720, fps=30.0):
    """
    Configure resolution and frame rate for FLIR camera.

    Args:
        cam (PySpin.CameraPtr): Initialized camera object.
        width (int): Desired image width in pixels.
        height (int): Desired image height in pixels.
        fps (float): Desired acquisition frame rate.

    Returns:
        None
    """
    nodemap = cam.GetNodeMap()

    # ----- Resolution: Width / Height -----
    width_node = PySpin.CIntegerPtr(nodemap.GetNode("Width"))
    height_node = PySpin.CIntegerPtr(nodemap.GetNode("Height"))

    if PySpin.IsWritable(width_node) and PySpin.IsWritable(height_node):
        max_w = width_node.GetMax()
        max_h = height_node.GetMax()

        # Clamp requested size to camera maximum
        width = min(width, max_w)
        height = min(height, max_h)

        # Some cameras require even values for width/height
        if width % 2 == 1:
            width -= 1
        if height % 2 == 1:
            height -= 1

        width_node.SetValue(width)
        height_node.SetValue(height)
        print(f"[INFO] Resolution set to {width} x {height}")
    else:
        print("[WARN] Width/Height not writable")

    # Optionally center ROI if OffsetX/OffsetY are available
    offset_x_node = PySpin.CIntegerPtr(nodemap.GetNode("OffsetX"))
    offset_y_node = PySpin.CIntegerPtr(nodemap.GetNode("OffsetY"))

    if PySpin.IsWritable(offset_x_node) and PySpin.IsWritable(offset_y_node):
        # Move ROI to center as best effort
        max_offset_x = offset_x_node.GetMax()
        max_offset_y = offset_y_node.GetMax()

        offset_x = max_offset_x // 2
        offset_y = max_offset_y // 2

        offset_x_node.SetValue(offset_x)
        offset_y_node.SetValue(offset_y)

    # ----- Frame rate: AcquisitionFrameRate -----
    enable_fps_node = PySpin.CBooleanPtr(nodemap.GetNode("AcquisitionFrameRateEnable"))
    if PySpin.IsWritable(enable_fps_node):
        enable_fps_node.SetValue(True)
    else:
        print("[WARN] AcquisitionFrameRateEnable not writable (might be always on).")

    fps_node = PySpin.CFloatPtr(nodemap.GetNode("AcquisitionFrameRate"))
    if PySpin.IsWritable(fps_node):
        max_fps = fps_node.GetMax()
        fps = min(fps, max_fps)
        fps_node.SetValue(fps)
        print(f"[INFO] Frame rate set to {fps:.2f} FPS")
    else:
        print("[WARN] Cannot set AcquisitionFrameRate.")

    # Debug print of applied values
    current_width = width_node.GetValue() if PySpin.IsReadable(width_node) else -1
    current_height = height_node.GetValue() if PySpin.IsReadable(height_node) else -1
    current_fps = fps_node.GetValue() if PySpin.IsReadable(fps_node) else -1.0
    print(f"[CHECK] Applied resolution: {current_width} x {current_height}, FPS: {current_fps:.2f}")


def start_continuous_mode(cam):
    """
    Set acquisition mode to Continuous and start acquisition.

    Args:
        cam (PySpin.CameraPtr): Initialized camera object.

    Returns:
        None
    """
    nodemap = cam.GetNodeMap()
    acquisition_mode = PySpin.CEnumerationPtr(nodemap.GetNode("AcquisitionMode"))
    if not PySpin.IsWritable(acquisition_mode):
        print("[ERROR] Cannot set AcquisitionMode to Continuous.")
        return

    cont_entry = acquisition_mode.GetEntryByName("Continuous")
    acquisition_mode.SetIntValue(cont_entry.GetValue())

    cam.BeginAcquisition()
    print("[INFO] Acquisition mode: Continuous")


def realtime_view_and_save(
    output_dir="captures",
    save_every_n_frames=10,
    window_name="FLIR Realtime",
    width=1280,
    height=720,
    fps=30.0,
):
    """
    Realtime camera streaming with GUI and automatic frame saving.

    Args:
        output_dir (str): Directory to save captured frames.
        save_every_n_frames (int): Save one frame every N frames.
        window_name (str): Name of the OpenCV window.
        width (int): Desired image width.
        height (int): Desired image height.
        fps (float): Desired frame rate.

    Returns:
        None
    """
    # Create output directory if not exists
    os.makedirs(output_dir, exist_ok=True)

    # ----- Step 1. Initialize system and get cameras -----
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()

    if cam_list.GetSize() == 0:
        print("[ERROR] No FLIR cameras found.")
        cam_list.Clear()
        system.ReleaseInstance()
        return

    cam = cam_list[0]

    try:
        # ----- Step 2. Init camera -----
        cam.Init()

        # ----- Step 3. PixelFormat setup -----
        print("[INFO] Before setting PixelFormat:")
        debug_pixel_format(cam)

        set_pixel_format(cam)

        print("[INFO] After setting PixelFormat:")
        debug_pixel_format(cam)

        # ----- Step 4. Configure resolution and FPS -----
        configure_camera_resolution_fps(cam, width=width, height=height, fps=fps)

        # ----- Step 5. Start continuous acquisition -----
        start_continuous_mode(cam)

        print("[INFO] Start realtime streaming. Press 'q' to quit.")
        print(f"[INFO] Auto save: every {save_every_n_frames} frames to directory: {output_dir}")

        frame_count = 0
        t0 = time.time()

        while True:
            # ----- Step 6. Grab next image -----
            image_result = cam.GetNextImage(1000)  # timeout 1000 ms

            if image_result.IsIncomplete():
                print(f"[WARN] Incomplete image. Status: {image_result.GetImageStatus()}")
                image_result.Release()
                continue

            frame_bgr = convert_image_to_bgr(image_result)
            image_result.Release()

            frame_count += 1
            elapsed = time.time() - t0
            fps_measured = frame_count / max(elapsed, 1e-6)

            # Draw FPS on frame
            cv2.putText(
                frame_bgr,
                f"FPS: {fps_measured:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2,
            )

            # ----- Step 7. Auto save every N-th frame -----
            if frame_count % save_every_n_frames == 0:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"frame_{timestamp}_{frame_count:06d}.png"
                save_path = os.path.join(output_dir, filename)
                cv2.imwrite(save_path, frame_bgr)
                print(f"[INFO] Saved frame #{frame_count} -> {save_path}")

            # ----- Step 8. Show realtime GUI -----
            cv2.imshow(window_name, frame_bgr)
            key = cv2.waitKey(1) & 0xFF

            # Press 'q' to quit
            if key == ord("q"):
                print("[INFO] 'q' pressed. Exiting loop.")
                break

    finally:
        # ----- Step 9. Cleanup -----
        try:
            cam.EndAcquisition()
        except PySpin.SpinnakerException:
            # If acquisition was not started correctly, ignore this error
            pass

        cam.DeInit()
        del cam
        cam_list.Clear()
        system.ReleaseInstance()
        cv2.destroyAllWindows()
        print("[INFO] Cleanup done.")


if __name__ == "__main__":
    # Example usage:
    # - Resolution: 1280x720
    # - Target FPS: 30
    # - Save every 10th frame
    realtime_view_and_save(
        output_dir="captures",
        save_every_n_frames=10,
        window_name="FLIR Realtime",
        width=1280,
        height=720,
        fps=30.0,
    )
