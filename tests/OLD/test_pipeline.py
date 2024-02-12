# %%
import PySpin
from nvuelab.utils import camera, video, clocks
import time
import cv2 as cv
from PIL import Image, ImageTk

# %%
recording_fps = 20

# %%
system, cam = camera.init()
FRAME_WIDTH, FRAME_HEIGHT, image_data = camera.get_frame_info(cam, True)

video_writer = video.video_writer_init(
    "test.mp4", recording_fps, FRAME_WIDTH, FRAME_HEIGHT
)
# %%

image = Image.fromarray(cv.cvtColor(image_data, cv.COLOR_BGR2RGB))
# %%
# recording

idle_status = False
camera.configure_trigger(cam, "hardware")
# %%

cam.BeginAcquisition()

while not idle_status:  # Changed to a while loop to continuously check for idle_status
    image_result = cam.GetNextImage()
    if image_result.IsIncomplete():
        print("Image incomplete with image status", image_result.GetImageStatus())
    else:
        # Assuming GetNDArray and the PixelFormat check are correct for your camera
        image_data = image_result.GetNDArray()
        if image_result.GetPixelFormat() != PySpin.PixelFormat_Mono8:
            # Conversion logic placeholder
            # You might need actual conversion code here if the pixel format isn't Mono8
            pass
            # Resize the image to match the video's frame size
        resized_image = cv.resize(image_data, (FRAME_WIDTH, FRAME_HEIGHT))
        cv.imshow("Video", resized_image)  # Use cv.imshow to display the image

    image_result.Release()  # This needs to be inside the loop to release each acquired image

    if cv.waitKey(1) & 0xFF == ord("q"):
        idle_status = True
        cv.destroyAllWindows()
        # Removed the 'break' as it's not needed with the 'while not idle_status' loop control


cam.EndAcquisition()
# %%
