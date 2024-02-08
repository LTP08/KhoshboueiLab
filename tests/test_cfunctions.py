# %%
from nvuelab.utils import camera
import PySpin


# %%
def get_first_frame_and_size():
    # Initialize the system
    system = PySpin.System.GetInstance()
    cam_list = system.GetCameras()
    if cam_list.GetSize() == 0:
        print("No camera detected.")
        system.ReleaseInstance()
        return None

    cam = cam_list.GetByIndex(0)
    cam.Init()

    # Configure the camera for software trigger
    camera.configure_trigger(cam, "software")

    # Start acquisition
    cam.BeginAcquisition()

    try:
        # Trigger the camera software trigger
        if (
            cam.TriggerSoftware is not None
            and cam.TriggerMode.GetValue() == PySpin.TriggerMode_On
        ):
            cam.TriggerSoftware.Execute()

        # Retrieve the next received image
        image_result = cam.GetNextImage()

        # Ensure image completion
        if image_result.IsIncomplete():
            print("Image incomplete with image status", image_result.GetImageStatus())
        else:
            # Extract image data
            width = image_result.GetWidth()
            height = image_result.GetHeight()
            print(f"Captured image size: {width}x{height}")

            # Example processing here

    finally:
        # End acquisition
        cam.EndAcquisition()
        cam.DeInit()
        del cam
        cam_list.Clear()
        system.ReleaseInstance()


if __name__ == "__main__":
    get_first_frame_and_size()

# %%
