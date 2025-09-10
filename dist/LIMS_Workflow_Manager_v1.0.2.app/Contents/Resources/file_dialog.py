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

if __name__ == "__main__":
    open_folder_dialog()