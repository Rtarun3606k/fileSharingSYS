#!/usr/bin/env python3
import tkinter as tk
import customtkinter as ctk
from src.client.gui import FileClientGUI

def main():
    # Create the root window
    root = ctk.CTk()
    
    # Create the client GUI
    app = FileClientGUI(root)
    
    # Start the main loop
    root.mainloop()

if __name__ == "__main__":
    main()