# %%
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import threading
import PySpin
from nvuelab.utils import camera
from PIL import Image, ImageTk
import cv2 as cv

# Placeholder for the system and cam variables
system = None
cam = None
acquisition_thread = None
idle_status = True  # Initially idle
video_label = None  # Placeholder for the video display label
save_directory = ""  # Variable to store the chosen directory


def init_camera():
    global system, cam, video_label
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
        record_button.config(state=tk.NORMAL)
    except Exception as e:
        messagebox.showerror(
            "Initialization Error",
            f"An error occurred during camera initialization: {e}",
        )


def display_first_frame():
    global cam, video_label
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


def choose_directory():
    global save_directory
    save_directory = filedialog.askdirectory()
    if save_directory:
        directory_label.config(text=f"Save Directory: {save_directory}")


def camera_acquisition():
    global idle_status, cam
    while not idle_status:
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
        image_result.Release()

        # This replaces cv.waitKey, as we're not using OpenCV's GUI functions
        root.update_idletasks()
        root.update()
        if idle_status:
            break  # If stop button pressed, exit the loop

    if cam is not None:
        cam.EndAcquisition()


def start_recording_thread():
    global acquisition_thread, idle_status, cam
    if idle_status:  # Start acquisition only if currently idle
        idle_status = False

        if acquisition_thread is not None:
            acquisition_thread.join()
            acquisition_thread = None

        camera.restart_camera(cam)
        cam.BeginAcquisition()

        acquisition_thread = threading.Thread(target=camera_acquisition)
        acquisition_thread.start()
        record_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
    else:
        messagebox.showerror("Error", f"Camera is already streaming. {idle_status}")


def stop_recording():
    global acquisition_thread, idle_status
    idle_status = True
    record_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)


def on_close():
    global system, cam, acquisition_thread, idle_status
    idle_status = True
    if cam is not None:

        if acquisition_thread is not None:
            acquisition_thread.join()
            acquisition_thread = None
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
init_button = tk.Button(root, text="Initialize Camera", command=init_camera)
init_button.pack()

# Directory selection
choose_button = tk.Button(root, text="Choose Directory", command=choose_directory)
choose_button.pack()
directory_label = tk.Label(root, text="No directory selected")
directory_label.pack()

# Recording controls
record_button = tk.Button(
    root, text="Start Streaming", state=tk.DISABLED, command=start_recording_thread
)
record_button.pack()
stop_button = tk.Button(
    root, text="Stop Streaming", state=tk.DISABLED, command=stop_recording
)
stop_button.pack()

root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()

# %%
