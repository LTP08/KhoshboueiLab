import time
from datetime import datetime
from typing import Union
from pathlib import Path
from dataclasses import dataclass
import toml


@dataclass
class Timer:
    """
    A simple timer class for measuring elapsed time and managing time-related operations.
    Attributes:
        start_time (float): The timestamp when the timer was started.
        duration (float): The total duration set for the timer, 0 by default for stopwatch mode.
        duration_units (str): The units of the duration, "seconds" by default.
        elapsed_time (float): The total time elapsed from the start until the timer was stopped.
        is_running (bool): Indicates whether the timer is currently running.
    """

    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    duration_units: str = "seconds"
    elapsed_time: float = 0.0
    is_running: bool = False

    def start(self):
        """Starts the timer by recording the current time. If the timer is already running, this method does nothing."""
        if not self.is_running:
            self.start_time = time.time()
            self.is_running = True
            print("Timer started")

    def stop(self):
        """Stops the timer and calculates the elapsed time. If the timer is not running, this method does nothing."""
        if self.is_running:
            self.elapsed_time = time.time() - self.start_time
            self.end_time = time.time()
            self.is_running = False
            print(f"Timer stopped, elapsed time: {self.elapsed_time:.2f} seconds")

    def restart(self):
        """Restarts the timer by resetting the elapsed time and starting the timer again."""
        self.start_time = time.time()
        self.elapsed_time = 0.0

    def reset(self):
        """Resets the timer to its initial state, clearing the start time, elapsed time, and stopping the timer if it is running."""
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.is_running = False
        print("Timer reset")

    def get_elapsed_time(self):
        """Retrieves the total time elapsed since the timer was started."""
        if self.is_running:
            return time.time() - self.start_time
        else:
            return self.elapsed_time

    def get_remaining_time(self):
        """Calculates and returns the remaining time before the timer reaches its duration."""
        if self.is_running and self.duration > 0:
            remaining_time = self.duration - (time.time() - self.start_time)
            if remaining_time <= 0:
                print("Timer has expired")
                return 0
            return remaining_time
        elif self.is_running and self.duration == 0:
            print("Duration is not set")
            return None
        else:
            print("Timer is not running")
            return None

    def print_time(self):
        """Prints the current elapsed time to the console."""
        print(
            f"\rElapsed time: {self.get_elapsed_time():.2f} seconds", end="", flush=True
        )


def format_timestamp(unix_timestamp: float) -> str:
    """Converts a Unix timestamp to a human-readable datetime string."""
    return datetime.fromtimestamp(unix_timestamp).strftime("%Y-%m-%d_%H:%M:%S")


def resolve_file_path(filepath: Union[Path, None]) -> Path:
    """Ensures a valid file path is returned, using a default if none is provided."""
    if filepath is None:
        filepath = Path.cwd() / "experiment-times.toml"
        print(f"Filepath not provided, using default: {filepath}")
    return filepath


def create_phase_name(phase_name: Union[str, None]) -> str:
    """Generates a unique phase name incorporating the current timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    return f"{phase_name}_{timestamp}" if phase_name else f"recording-{timestamp}"


def save_timer_state(
    timer: Timer, phase: Union[str, None] = None, filepath: Union[Path, None] = None
):
    """Appends or updates the state of a Timer object in a TOML file, handling specific file and serialization exceptions."""
    try:
        filepath = resolve_file_path(filepath)
        phase_name = create_phase_name(phase)

        # Attempt to load existing data or initialize an empty dictionary
        data = {}
        if filepath.exists():
            with open(filepath, "r", encoding="utf-8") as file:
                data = toml.load(file)

        # Update data with the new timer state
        data[phase_name] = {
            "start_time": format_timestamp(timer.start_time),
            "end_time": format_timestamp(timer.end_time),
            "duration": timer.duration,
            "duration_units": timer.duration_units,
            "elapsed_time": timer.elapsed_time,
        }

        # Write the updated data back to the file
        with open(filepath, "w", encoding="utf-8") as file:
            toml.dump(data, file)

    except FileNotFoundError:
        print(f"File not found: {filepath}")
    except PermissionError:
        print(f"Permission denied: {filepath}")
    except toml.TomlDecodeError:
        print(f"Error decoding TOML from {filepath}")
    except IOError as e:
        print(f"I/O error({e.errno}): {e.strerror}")
