import PySpin


def print_camera_info(cam):
    """
    Args:
        cam (PySpin.CameraPtr): Initialized camera object.

    Returns:
        None
    """
    nodemap_tldevice = cam.GetTLDeviceNodeMap()

    model_name_node = PySpin.CStringPtr(nodemap_tldevice.GetNode("DeviceModelName"))
    serial_node = PySpin.CStringPtr(nodemap_tldevice.GetNode("DeviceSerialNumber"))
    vendor_node = PySpin.CStringPtr(nodemap_tldevice.GetNode("DeviceVendorName"))

    model_name = model_name_node.GetValue() if PySpin.IsReadable(model_name_node) else "Unknown"
    serial = serial_node.GetValue() if PySpin.IsReadable(serial_node) else "Unknown"
    vendor = vendor_node.GetValue() if PySpin.IsReadable(vendor_node) else "Unknown"

    print("=== Camera Information ===")
    print(f"  Vendor : {vendor}")
    print(f"  Model  : {model_name}")
    print(f"  Serial : {serial}")


def lab1_camera_info():
    """
    Args:
        None

    Returns:
        None
    """
    # 1) Get system and camera list
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()

    num_cams = cam_list.GetSize()
    print(f"[INFO] Number of FLIR cameras detected: {num_cams}")

    if num_cams == 0:
        cam_list.Clear()
        system.ReleaseInstance()
        return

    cam = cam_list[0]

    try:
        # 2) Init camera
        cam.Init()

        # 3) Print info
        print_camera_info(cam)

    finally:
        # 4) Proper cleanup in correct order
        cam.DeInit()
        del cam         # remove Python reference

        cam_list.Clear()
        system.ReleaseInstance()


if __name__ == "__main__":
    lab1_camera_info()
