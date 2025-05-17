import os
import sys


def resource_path(relative_path):
    """Get the absolute path to a resource, works for development and PyInstaller."""

    if hasattr(sys, "_MEIPASS"):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        # Path when running the script directly (development)
        base_path = os.path.abspath(".")

    # Resulting path
    return os.path.join(base_path, relative_path)
