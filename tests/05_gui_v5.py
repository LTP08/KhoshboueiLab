# %%
# Works for one recording

import os
import time
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import (
    filedialog,
    messagebox,
    simpledialog,
    BooleanVar,
    Label,
    Button,
    Checkbutton,
)
import threading
import PySpin
from nvuelab.utils import camera, video
from PIL import Image, ImageTk
import cv2 as cv

# Placeholder for the system and cam variables
system = None
cam = None
acquisition_thread = None
idle_status = True  # Initially idle
video_label = None  # Placeholder for the video display label
video_writer = None  # Placeholder for the video writer
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
            index = 0  # Automatically select the only camera

        cam = cam_list.GetByIndex(index)
        cam.Init()

        # Display the first frame after camera initialization
        display_first_frame()
        camera.configure_trigger(cam, "hardware")
        # Enable the "Record" button upon successful camera initialization

        # Initialize video writer
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
    if image_data is not None and image_data.size > 0:
        image = Image.fromarray(cv.cvtColor(image_data, cv.COLOR_BGR2RGB))
        photo = ImageTk.PhotoImage(image=image)
        if video_label is None:
            video_label = tk.Label(root, image=photo)
            video_label.image = photo  # Keep a reference!
            video_label.pack(expand=True)
        else:
            video_label.config(image=photo)
            video_label.image = photo


def camera_acquisition():
    global system, cam, video_writer, idle_status

    while not idle_status:
        if idle_status:
            break  # If stop button pressed, exit the loop
        if cam is None:
            break  # Safety check

        image_result = cam.GetNextImage()
        if image_result.IsIncomplete():
            print("Image incomplete with image status", image_result.GetImageStatus())
        else:
            image_data = image_result.GetNDArray()
            image = Image.fromarray(cv.cvtColor(image_data, cv.COLOR_BGR2RGB))
            photo = ImageTk.PhotoImage(image=image)
            video_label.config(image=photo)
            video_label.image = photo  # Keep a reference!
            if video_writer is not None:
                video.save_video(video_writer, image_data)
        image_result.Release()
        # This replaces cv.waitKey, as we're not using OpenCV's GUI functions
        root.update_idletasks()
        root.update()

    if cam is not None:
        cam.EndAcquisition()


def start_recording_thread():
    global system, cam, acquisition_thread, idle_status, cam, system
    time.sleep(0.2)
    if acquisition_thread is not None:
        acquisition_thread.join()
        acquisition_thread = None
    if idle_status:  # Start acquisition only if currently idle
        idle_status = False
        camera.restart_camera(cam)
        cam.BeginAcquisition()
        save_video()
        acquisition_thread = threading.Thread(target=camera_acquisition)
        acquisition_thread.start()
        record_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
    else:
        messagebox.showerror("Error", f"Camera is already streaming. {idle_status}")


def stop_recording():
    global idle_status, video_writer, acquisition_thread
    idle_status = True
    if video_writer is not None:
        video_writer.release()
        video_writer = None
        time.sleep(0.5)
    record_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)


def on_close():
    global system, cam, acquisition_thread, idle_status, video_writer
    idle_status = True

    if video_writer is not None:
        video_writer.release()
        video_writer = None

    if acquisition_thread is not None:
        acquisition_thread.join()
        acquisition_thread = None
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

# Initialize Camera button
init_button = Button(root, text="Initialize Camera", command=init_camera)
init_button.pack()

# Directory selection
choose_button = Button(root, text="Choose Directory", command=choose_directory)
choose_button.pack()
directory_label = Label(root, text="No directory selected")
directory_label.pack()

# Recording controls
record_button = Button(
    root, text="Start Streaming", state=tk.DISABLED, command=start_recording_thread
)
record_button.pack()
stop_button = Button(
    root, text="Stop Streaming", state=tk.DISABLED, command=stop_recording
)
stop_button.pack()

root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()
# %%
