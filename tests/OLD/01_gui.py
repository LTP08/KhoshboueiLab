# %%
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, Label
import threading
import PySpin
from nvuelab.utils import camera, video, clocks
from PIL import Image, ImageTk
import cv2 as cv


# Placeholder for the system and cam variables
system = None
cam = None
acquisition_thread = None
idle_status = True  # Initially idle


def init_camera():
    global system, cam
    try:
        system = PySpin.System.GetInstance()
        cam_list = system.GetCameras()
        size = cam_list.GetSize()

        if size == 0:
            tk.messagebox.showerror("Error", "No cameras detected.")
            return
        elif size > 1:
            index = simpledialog.askinteger(
                "Select Camera",
                "Multiple cameras detected. Enter the camera index to use (0 to {}):".format(
                    size - 1
                ),
                minvalue=0,
                maxvalue=size - 1,
            )
            if index is None:  # User cancelled the dialog
                print("Camera selection cancelled.")
                return
        else:
            index = 0  # Automatically select the only camera

        cam = cam_list.GetByIndex(index)
        cam.Init()
        device_model_name, device_serial_number = camera.get_camera_info(cam)
        print(
            f"Camera Model Loaded: {device_model_name}, Serial Number: {device_serial_number}"
        )

        # Display the first frame after camera initialization
        display_first_frame()

        # Enable the "Record" button upon successful camera initialization
        record_button.config(state=tk.NORMAL)
    except Exception as e:
        tk.messagebox.showerror(
            "Initialization Error",
            f"An error occurred during camera initialization: {e}",
        )


def display_first_frame():
    global cam, root
    FRAME_WIDTH, FRAME_HEIGHT, image_data = camera.get_frame_info(cam, plot=True)
    # Ensure image_data is not None and is an array before proceeding
    if image_data is not None and image_data.size > 0:
        # Convert to a PIL Image
        image = Image.fromarray(cv.cvtColor(image_data, cv.COLOR_BGR2RGB))
        image_resized = image.resize((1920, 1080), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image=image_resized)

        # Display the image in the center of the window
        image_label = tk.Label(root, image=photo)
        image_label.image = photo  # Keep a reference!
        image_label.pack(expand=True)

        # Adjust the main window size
        root.geometry("1920x1080")


def choose_directory():
    directory = filedialog.askdirectory()
    if directory:
        directory_label.config(text=directory)


def camera_acquisition():
    global idle_status, cam
    global FRAME_WIDTH, FRAME_HEIGHT
    # Create a label to display the images if not already created. Assuming this is global.
    global video_label
    if "video_label" not in globals():
        video_label = tk.Label(root)
        video_label.pack()

    if cam is not None:
        cam.BeginAcquisition()

    while not idle_status:
        if cam is None:
            break  # Safety check
        image_result = cam.GetNextImage()
        if image_result.IsIncomplete():
            print("Image incomplete with image status", image_result.GetImageStatus())
        else:
            image_data = image_result.GetNDArray()
            # Convert to a format that can be displayed by Tkinter
            image = Image.fromarray(cv.cvtColor(image_data, cv.COLOR_BGR2RGB))
            photo = ImageTk.PhotoImage(
                image=image.resize((1920, 1080), Image.Resampling.LANCZOS)
            )

            video_label.config(image=photo)
            video_label.image = photo  # Keep a reference!

        image_result.Release()

        # This replaces cv.waitKey, as we're not using OpenCV's GUI functions
        root.update_idletasks()
        root.update()

    if cam is not None:
        cam.EndAcquisition()


def start_recording_thread():
    global acquisition_thread, idle_status
    idle_status = False  # Allow the acquisition loop to run
    acquisition_thread = threading.Thread(target=camera_acquisition)
    acquisition_thread.start()
    record_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL)
    init_button.config(state=tk.DISABLED)


def stop_recording():
    global acquisition_thread, idle_status  # Declare global variables
    idle_status = True  # Signal the acquisition loop to stop
    if acquisition_thread is not None:
        acquisition_thread.join()  # Wait for the acquisition loop to exit
        acquisition_thread = None  # Reset the acquisition_thread variable
    if cam is not None:
        # Ensures cam.EndAcquisition() is called after the thread has finished
        cam.EndAcquisition()
    record_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.DISABLED)
    init_button.config(state=tk.NORMAL)  # Re-enable init button


def on_close():
    stop_recording()  # Make sure to stop recording and release resources
    if cam is not None:
        cam.DeInit()
        del cam
        cam = None
    if system is not None:
        system.ReleaseInstance()
        del system
        system = None
    root.destroy()


# Create the main window
root = tk.Tk()
root.title("Video Save Directory Selector")
root.geometry("500x250")

# Frames for organizing layout
top_frame = tk.Frame(root)
top_frame.pack(side=tk.TOP, fill=tk.X, padx=20, pady=20)
bottom_frame = tk.Frame(root)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)

# Initialize Camera button
init_button = tk.Button(top_frame, text="Initialize Camera", command=init_camera)
init_button.pack(side=tk.LEFT)

# Directory selection
choose_button = tk.Button(top_frame, text="Choose Directory", command=choose_directory)
choose_button.pack(side=tk.LEFT, padx=10)
directory_label = tk.Label(top_frame, text="No directory selected")
directory_label.pack(side=tk.LEFT)

# Recording controls
record_button = tk.Button(
    bottom_frame, text="Record", state=tk.DISABLED, command=start_recording_thread
)
record_button.pack(side=tk.LEFT, padx=5)
stop_button = tk.Button(
    bottom_frame, text="Stop Recording", state=tk.DISABLED, command=stop_recording
)
stop_button.pack(side=tk.LEFT)

root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()

# %%
