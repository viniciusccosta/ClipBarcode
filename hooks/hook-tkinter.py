# PyInstaller hook for better Tkinter icon handling on macOS
from PyInstaller.utils.hooks import collect_data_files

# Ensure icon files are properly included
datas = collect_data_files("assets")
