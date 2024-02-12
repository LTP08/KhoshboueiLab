# %%
import os
import time
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, Label, Button
import threading
from queue import Queue
import PySpin
from nvuelab.utils import camera, video
from PIL import Image, ImageTk
import cv2 as cv

# Global variables initialization
system = None
cam = None
acquisition_thread = None
idle_event = threading.Event()  # Use Event for thread synchronization
image_queue = Queue()  # Queue for thread-safe GUI updates
video_label = None
video_writer = None
FRAME_HEIGHT = 0
FRAME_WIDTH = 0
save_video_path = ""


def choose_directory():
    global save_video_path
    new_directory = filedialog.askdirectory()
    if new_directory:
        save_video_path = new_directory
        directory_label.config(text=f"Save Directory: {save_video_path}")


def save_video():
    global video_writer, save_video_path, FRAME_WIDTH, FRAME_HEIGHT

    if video_writer is not None:
        video_writer.release()
        video_writer = None

    if video_writer is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        video_filename = os.path.join(save_video_path, f"video_{timestamp}.mp4")
        video_writer = video.video_writer_init(
            video_filename, 20, FRAME_WIDTH, FRAME_HEIGHT
        )


def init_camera():
    global system, cam, video_label, video_writer, FRAME_HEIGHT, FRAME_WIDTH, save_video_path
    try:
        system = PySpin.System.GetInstance()
        cam_list = system.GetCameras()
        num_cameras = cam_list.GetSize()

        if num_cameras == 0:
            messagebox.showerror("Error", "No cameras detected.")
            return
        elif num_cameras > 1:
            index = simpledialog.askinteger(
                "Select Camera",
                "Multiple cameras detected. Enter the camera index to use (0 to {}):".format(
                    num_cameras - 1
                ),
                minvalue=0,
                maxvalue=num_cameras - 1,
            )
            if index is None:  # User cancelled the dialog
                print("Camera selection cancelled.")
                return
        else:
            index = 0

        cam = cam_list.GetByIndex(index)
        cam.Init()

        display_first_frame()
        camera.configure_trigger(cam, "hardware")

        save_video_path = Path.home()
        directory_label.config(text=f"Save Directory: {save_video_path}")

        record_button.config(state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror(
            "Initialization Error",
            f"An error occurred during camera initialization: {e}",
        )


def display_first_frame():
    global cam, video_label, FRAME_HEIGHT, FRAME_WIDTH
    FRAME_WIDTH, FRAME_HEIGHT, image_data = camera.get_frame_info(cam, plot=True)
    FRAME_WIDTH = 1920
    FRAME_HEIGHT = 1080
    if image_data is not None and image_data.size > 0:
        resized_image = cv.resize(image_data, (FRAME_WIDTH, FRAME_HEIGHT))
        image = Image.fromarray(cv.cvtColor(resized_image, cv.COLOR_BGR2RGB))
        photo = ImageTk.PhotoImage(image=image)
        if video_label is None:
            video_label = tk.Label(root, image=photo)
            video_label.image = photo
            video_label.pack(expand=True)
        else:
            video_label.config(image=photo)
            video_label.image = photo


def camera_acquisition():
    global system, cam, video_writer
    image_result = (
        None  # Initialize to None to ensure it's defined for the finally block
    )

    while not idle_event.is_set():
        try:
            if cam.IsStreaming():
                image_result = cam.GetNextImage(5000)  # Adjust timeout as needed
                if image_result.IsIncomplete():
                    print(
                        "Image incomplete with image status",
                        image_result.GetImageStatus(),
                    )
                else:
                    image_data = image_result.GetNDArray()
                    resized_image = cv.resize(image_data, (FRAME_WIDTH, FRAME_HEIGHT))
                    image_queue.put(resized_image)
                    if video_writer is not None:
                        video.save_video(video_writer, resized_image)
            else:
                break  # Exit loop if the camera stops streaming

        except PySpin.SpinnakerException as ex:
            # Handle specific timeout exception or general failure
            print(f"Failed to get next image: {ex}")
            # Decide on specific actions here, like attempting to reconnect, logging, or breaking the loop

        finally:
            # Check if image_result is not None and is valid before attempting to release
            if image_result is not None and image_result.IsValid():
                image_result.Release()

    if cam is not None:
        cam.EndAcquisition()


def update_gui():
    try:
        while not image_queue.empty():
            image_data = image_queue.get_nowait()
            image = Image.fromarray(cv.cvtColor(image_data, cv.COLOR_BGR2RGB))
            photo = ImageTk.PhotoImage(image=image)
            video_label.config(image=photo)
            video_label.image = photo
    finally:
        root.after(1, update_gui)


def start_recording_thread():
    global system, cam, acquisition_thread, video_writer
    if not idle_event.is_set():
        messagebox.showerror("Error", "Camera is already streaming.")
        return
    if acquisition_thread is not None:
        acquisition_thread.join()
    idle_event.clear()
    camera.restart_camera(cam)
    cam.BeginAcquisition()
    save_video()
    acquisition_thread = threading.Thread(target=camera_acquisition)
    acquisition_thread.start()
    record_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)


def stop_recording():
    # Signal the acquisition loop to stop
    global system, cam, acquisition_thread, video_writer
    idle_event.set()

    # Wait for the acquisition thread to finish
    if acquisition_thread is not None:
        acquisition_thread.join()

    # Check if the camera is still acquiring images and stop it
    if cam is not None and cam.IsStreaming():
        cam.EndAcquisition()

    # Release the video writer if it's being used
    if video_writer is not None:
        video_writer.release()
        video_writer = None

    # Reset UI elements (e.g., disable the stop button and enable the start button)
    record_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)

    print("Acquisition stopped and resources released.")


def on_close():
    global system, cam, acquisition_thread, video_writer
    idle_event.set()
    if acquisition_thread is not None:
        acquisition_thread.join()
    if video_writer is not None:
        video_writer.release()
    if cam is not None:
        if cam.IsStreaming():
            cam.EndAcquisition()
        cam.DeInit()
        del cam
    if system is not None:
        system.ReleaseInstance()
        del system
    root.destroy()


# Create the main window
root = tk.Tk()
root.title("Camera Stream Viewer")
root.geometry("800x600")

# Initialize GUI components
init_button = Button(root, text="Initialize Camera", command=init_camera)
init_button.pack()
choose_button = Button(root, text="Choose Directory", command=choose_directory)
choose_button.pack()
directory_label = Label(root, text="No directory selected")
directory_label.pack()
record_button = Button(
    root, text="Start Streaming", state=tk.DISABLED, command=start_recording_thread
)
record_button.pack()
stop_button = Button(
    root, text="Stop Streaming", state=tk.DISABLED, command=stop_recording
)
stop_button.pack()

root.protocol("WM_DELETE_WINDOW", on_close)

idle_event.set()  # Initially idle
root.after(100, update_gui)  # Start the GUI update loop

root.mainloop()

# %%
