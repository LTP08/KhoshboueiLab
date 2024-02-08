# %%
from datetime import datetime
import cv2 as cv
import PySpin
from nvuelab.utils import camera

# %%
NUM_IMAGES = int(20 * 60)  # Set the desired number of images
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
VIDEO_FILENAME = f"output_video_{timestamp}.mp4"
FRAME_WIDTH = 1920  # Adjust to your camera's resolution
FRAME_HEIGHT = 1080  # Adjust to your camera's resolution
FPS = 20  # Adjust based on your acquisition speed

# Initialize the system and camera
system = PySpin.System.GetInstance()
cam_list = system.GetCameras()
cam = cam_list.GetByIndex(0)
cam.Init()

# Configure the camera for hardware trigger
cam.TriggerMode.SetValue(PySpin.TriggerMode_Off)
cam.TriggerSource.SetValue(PySpin.TriggerSource_Line2)
cam.TriggerActivation.SetValue(PySpin.TriggerActivation_RisingEdge)
cam.TriggerMode.SetValue(PySpin.TriggerMode_On)
# %%
# Start the acquisition
cam.BeginAcquisition()

# Setup video writer
fourcc = cv.VideoWriter_fourcc(*"mp4v")
video_writer = cv.VideoWriter(
    VIDEO_FILENAME, fourcc, FPS, (FRAME_WIDTH, FRAME_HEIGHT), False
)

for i in range(NUM_IMAGES):
    print(f"Waiting for image {i+1} of {NUM_IMAGES}")

    # Wait for hardware trigger and capture an image
    image_result = cam.GetNextImage()

    if image_result.IsIncomplete():
        print("Image incomplete with image status", image_result.GetImageStatus())
    else:
        image_data = image_result.GetNDArray()
        if image_result.GetPixelFormat() != PySpin.PixelFormat_Mono8:
            # Conversion logic placeholder
            pass

        # Resize the image to match the video's frame size
        resized_image = cv.resize(image_data, (FRAME_WIDTH, FRAME_HEIGHT))

        # Display the frame live
        cv.imshow("Live Video", resized_image)

        # Write the frame to the video
        video_writer.write(resized_image)

        print(f"Image {i+1} captured")

    # Release the image
    image_result.Release()

    # Break the loop if the user presses "q"
    if cv.waitKey(1) & 0xFF == ord("q"):
        break

# Cleanup
video_writer.release()
cam.EndAcquisition()
cam.DeInit()
del cam
cam_list.Clear()
system.ReleaseInstance()
cv.destroyAllWindows()

print(f"Video saved as {VIDEO_FILENAME}")

# %%
