# %%
import PySpin

NUM_IMAGES = 20  # Set the desired number of images
# %%
# Initialize the system and camera
system = PySpin.System.GetInstance()
cam_list = system.GetCameras()
cam = cam_list.GetByIndex(0)
cam.Init()

# Configure the camera for hardware trigger
cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
cam.TriggerSource.SetValue(PySpin.TriggerSource_Line2)  # Adjust based on your setup
cam.TriggerActivation.SetValue(PySpin.TriggerActivation_RisingEdge)  # Adjust as needed
cam.TriggerMode.SetValue(PySpin.TriggerMode_On)

# Start the acquisition
cam.BeginAcquisition()

for i in range(NUM_IMAGES):
    print(f"Waiting for image {i+1} of {NUM_IMAGES}")

    # Wait for hardware trigger and capture an image
    image_result = cam.GetNextImage()

    # Check if the image is complete
    if image_result.IsIncomplete():
        print("Image incomplete with image status", image_result.GetImageStatus())
    else:
        # Create an ImageProcessor object for image conversion
        image_processor = PySpin.ImageProcessor()

        # Determine if image conversion is needed
        if image_result.GetPixelFormat() != PySpin.PixelFormat_Mono8:
            # Convert the image to Mono8 using the ImageProcessor
            image_converted = image_processor.Convert(
                image_result, PySpin.PixelFormat_Mono8
            )
        else:
            image_converted = image_result

        # Save the image
        filename = f"TriggeredImage_{i+1}.jpg"
        image_converted.Save(filename)
        print(f"Image {i+1} saved at {filename}")

    # Release the image
    image_result.Release()

# End the acquisition
cam.EndAcquisition()

# Deinitialize the camera
cam.DeInit()
del cam

# Clear the camera list and release the system instance
cam_list.Clear()
system.ReleaseInstance()

# %%
