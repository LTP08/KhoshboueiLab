import PySpin


def init():
    # you have to return system for it to work :)
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    size = cam_list.GetSize()
    index = 0  # Default index for the first camera

    if size > 1:
        print("Multiple cameras detected.")
        print_camera_list(cam_list)
        while True:  # Keep asking until a valid input is received
            user_input = input("Enter the camera index to use: ")
            try:
                index = int(user_input)  # Attempt to convert the input to an integer
                if 0 <= index < size:  # Check if the input is within the valid range
                    break  # Exit the loop if the input is valid
                else:
                    print(f"Please enter a number between 0 and {size-1}.")
            except ValueError:  # Catch the exception if conversion to integer fails
                print("Invalid input. Please enter a valid number.")

    cam = cam_list.GetByIndex(index)
    cam.Init()
    device_model_name, device_serial_number = get_camera_info(cam)
    # Print camera information
    print(
        f"Camera Model Loaded: {device_model_name}, Serial Number: {device_serial_number}"
    )
    return system, cam


def restart_camera(cam: PySpin.CameraPtr):
    if cam.IsStreaming():
        # Stop acquisition if the camera is currently streaming
        cam.EndAcquisition()
        print("Camera stopped")


def get_frame_info(cam: PySpin.CameraPtr):
    # Ensure the camera is not acquiring
    restart_camera(cam)
    configure_trigger(cam, "software")
    # Start acquisition for capturing frame info
    cam.BeginAcquisition()

    try:
        # Software trigger if applicable
        if cam.TriggerMode.GetValue() == PySpin.TriggerMode_On:
            cam.TriggerSoftware.Execute()

        image_result = cam.GetNextImage()
        if image_result.IsIncomplete():
            print(f"Image incomplete with image status {image_result.GetImageStatus()}")
        else:
            width = image_result.GetWidth()
            height = image_result.GetHeight()
            print(f"Captured image size: {width}x{height}")
            return width, height
    finally:
        # Always ensure to end acquisition to reset the camera state
        cam.EndAcquisition()


def configure_trigger(cam: PySpin.PySpin.CameraPtr, trigger: str):
    if trigger == "hardware":
        # Configure for hardware trigger
        cam.TriggerMode.SetValue(
            PySpin.TriggerMode_Off
        )  # Ensure trigger mode is off when making changes
        cam.TriggerSource.SetValue(
            PySpin.TriggerSource_Line2
        )  # Adjust based on your setup
        cam.TriggerActivation.SetValue(PySpin.TriggerActivation_RisingEdge)
        cam.TriggerMode.SetValue(PySpin.TriggerMode_On)
    elif trigger == "software":
        # Configure for software trigger
        cam.TriggerMode.SetValue(
            PySpin.TriggerMode_Off
        )  # Ensure trigger mode is off when making changes
        cam.TriggerSource.SetValue(PySpin.TriggerSource_Software)
        cam.TriggerMode.SetValue(PySpin.TriggerMode_On)
    else:
        print(f"Unknown trigger type: {trigger}")


def get_camera_info(cam: PySpin.CameraPtr):
    nodemap_tldevice = cam.GetTLDeviceNodeMap()

    device_model_name = PySpin.CStringPtr(
        nodemap_tldevice.GetNode("DeviceModelName")
    ).GetValue()
    device_serial_number = PySpin.CStringPtr(
        nodemap_tldevice.GetNode("DeviceSerialNumber")
    ).GetValue()
    # Print camera information
    return device_model_name, device_serial_number


# aux functions
def print_camera_list(cam_list: PySpin.CameraList):
    size = cam_list.GetSize()
    for i in range(size):
        cam = cam_list.GetByIndex(i)
        device_model_name, device_serial_number = get_camera_info(cam)
        # Print camera information
        print(
            f"[{i}]: Model: {device_model_name}, Serial Number: {device_serial_number}"
        )
