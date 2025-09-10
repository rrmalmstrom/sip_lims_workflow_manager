import tkinter as tk
from tkinter import filedialog

def open_folder_dialog():
    """
    Opens a native OS folder selection dialog and prints the selected path.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main tkinter window
    folder_path = filedialog.askdirectory(master=root)
    root.destroy()
    if folder_path:
        print(folder_path)

def open_file_dialog():
    """
    Opens a native OS file selection dialog and prints the selected path.
    """
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(master=root)
    root.destroy()
    if file_path:
        print(file_path)

if __name__ == "__main__":
    # This script can now be called with an argument to determine which dialog to open.
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'file':
        open_file_dialog()
    else:
        open_folder_dialog()