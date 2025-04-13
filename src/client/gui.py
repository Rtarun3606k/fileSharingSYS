import os
import sys
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path

# Add parent directory to path for importing client module
sys.path.append(str(Path(__file__).resolve().parent.parent))
from client.client import FileClient

class FileClientGUI:
    def __init__(self, root):
        """
        Initialize the file client GUI.
        
        Args:
            root: The root window
        """
        self.root = root
        self.client = FileClient()
        
        # Set up the GUI
        self.root.title("Secure File Sharing Client")
        self.root.geometry("900x600")
        
        # Set the theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create connection frame
        self.connection_frame = ctk.CTkFrame(self.main_frame)
        self.connection_frame.pack(fill="x", padx=10, pady=10)
        
        # Server address input
        ctk.CTkLabel(self.connection_frame, text="Server Address:").pack(side="left", padx=5)
        self.server_entry = ctk.CTkEntry(self.connection_frame, width=200)
        self.server_entry.pack(side="left", padx=5)
        self.server_entry.insert(0, "localhost")
        
        # Server port input
        ctk.CTkLabel(self.connection_frame, text="Port:").pack(side="left", padx=5)
        self.port_entry = ctk.CTkEntry(self.connection_frame, width=80)
        self.port_entry.pack(side="left", padx=5)
        self.port_entry.insert(0, "9000")
        
        # Connect button
        self.connect_btn = ctk.CTkButton(
            self.connection_frame,
            text="Connect",
            command=self.toggle_connection
        )
        self.connect_btn.pack(side="left", padx=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(self.connection_frame, text="Not Connected")
        self.status_label.pack(side="left", padx=10)
        
        # Create file list frame
        self.file_frame = ctk.CTkFrame(self.main_frame)
        self.file_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # File list label
        ctk.CTkLabel(self.file_frame, text="Files on Server:", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)
        
        # Create a frame for the file list with scrollbars
        self.file_list_frame = ctk.CTkFrame(self.file_frame)
        self.file_list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Create a scrollable frame
        self.file_list_scrollable = ctk.CTkScrollableFrame(self.file_list_frame)
        self.file_list_scrollable.pack(fill="both", expand=True)
        
        # File list (will be populated with CTkFrames for each file)
        self.file_list_widgets = []
        
        # Create bottom frame for buttons
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(fill="x", padx=10, pady=10)
        
        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            self.button_frame,
            text="Refresh File List",
            command=self.refresh_file_list,
            state="disabled"
        )
        self.refresh_btn.pack(side="left", padx=5)
        
        # Upload button
        self.upload_btn = ctk.CTkButton(
            self.button_frame,
            text="Upload File",
            command=self.upload_file,
            state="disabled"
        )
        self.upload_btn.pack(side="left", padx=5)
        
        # Change download dir button
        self.download_dir_btn = ctk.CTkButton(
            self.button_frame,
            text="Change Download Directory",
            command=self.change_download_dir
        )
        self.download_dir_btn.pack(side="left", padx=5)
        
        # Download directory label
        self.download_dir_label = ctk.CTkLabel(
            self.button_frame,
            text=f"Download Directory: {self.client.download_dir}"
        )
        self.download_dir_label.pack(side="left", padx=5)
    
    def toggle_connection(self):
        """
        Toggle connection to the server.
        """
        if not self.client.connected:
            # Connect to server
            host = self.server_entry.get().strip()
            port_str = self.port_entry.get().strip()
            
            try:
                port = int(port_str)
            except ValueError:
                messagebox.showerror("Error", "Port must be a number")
                return
            
            # Disable UI during connection attempt
            self.connect_btn.configure(state="disabled")
            self.status_label.configure(text="Connecting...")
            
            # Run connection in separate thread to avoid freezing the UI
            threading.Thread(target=self._connect_thread, args=(host, port), daemon=True).start()
        else:
            # Disconnect from server
            self.client.disconnect()
            self.update_connection_state(False)
    
    def _connect_thread(self, host, port):
        """
        Connect to the server in a separate thread.
        """
        success = self.client.connect(host, port)
        
        # Update the UI in the main thread
        self.root.after(0, lambda: self.update_connection_state(success))
        
        if success:
            self.root.after(0, self.refresh_file_list)
    
    def update_connection_state(self, connected):
        """
        Update the UI based on connection state.
        """
        if connected:
            self.status_label.configure(text="Connected")
            self.connect_btn.configure(text="Disconnect", state="normal")
            self.refresh_btn.configure(state="normal")
            self.upload_btn.configure(state="normal")
        else:
            self.status_label.configure(text="Not Connected")
            self.connect_btn.configure(text="Connect", state="normal")
            self.refresh_btn.configure(state="disabled")
            self.upload_btn.configure(state="disabled")
            self.clear_file_list()
    
    def refresh_file_list(self):
        """
        Refresh the file list from the server.
        """
        if not self.client.connected:
            return
        
        # Clear current file list
        self.clear_file_list()
        
        # Show loading indicator
        loading_label = ctk.CTkLabel(self.file_list_scrollable, text="Loading files...")
        loading_label.pack(pady=20)
        self.file_list_widgets.append(loading_label)
        
        # Get files in separate thread
        threading.Thread(target=self._refresh_thread, daemon=True).start()
    
    def _refresh_thread(self):
        """
        Get file list from server in a separate thread.
        """
        file_list = self.client.get_file_list()
        
        # Update the UI in the main thread
        self.root.after(0, lambda: self.update_file_list(file_list))
    
    def update_file_list(self, file_list):
        """
        Update the file list UI.
        """
        # Clear the current file list including loading indicator
        self.clear_file_list()
        
        if not file_list:
            # No files found
            no_files_label = ctk.CTkLabel(
                self.file_list_scrollable,
                text="No files found on the server"
            )
            no_files_label.pack(pady=20)
            self.file_list_widgets.append(no_files_label)
            return
        
        # Add header row
        header_frame = ctk.CTkFrame(self.file_list_scrollable)
        header_frame.pack(fill="x", pady=5)
        self.file_list_widgets.append(header_frame)
        
        ctk.CTkLabel(header_frame, text="File Name", font=("Arial", 12, "bold"), width=400).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Size", font=("Arial", 12, "bold"), width=100).pack(side="left", padx=5)
        ctk.CTkLabel(header_frame, text="Action", font=("Arial", 12, "bold"), width=100).pack(side="left", padx=5)
        
        # Add a separator line
        separator = ctk.CTkFrame(self.file_list_scrollable, height=1, fg_color="gray")
        separator.pack(fill="x", pady=5)
        self.file_list_widgets.append(separator)
        
        # Add files
        for file_info in file_list:
            file_frame = ctk.CTkFrame(self.file_list_scrollable)
            file_frame.pack(fill="x", pady=2)
            self.file_list_widgets.append(file_frame)
            
            filename = file_info.get("name", "Unknown")
            size = file_info.get("size_formatted", "Unknown")
            
            ctk.CTkLabel(file_frame, text=filename, width=400).pack(side="left", padx=5)
            ctk.CTkLabel(file_frame, text=size, width=100).pack(side="left", padx=5)
            
            download_btn = ctk.CTkButton(
                file_frame,
                text="Download",
                width=100,
                command=lambda fname=filename: self.download_file(fname)
            )
            download_btn.pack(side="left", padx=5)
    
    def clear_file_list(self):
        """
        Clear the file list UI.
        """
        for widget in self.file_list_widgets:
            widget.destroy()
        
        self.file_list_widgets = []
    
    def download_file(self, filename):
        """
        Download a file from the server.
        """
        if not self.client.connected:
            return
        
        # Show a loading dialog
        loading_dialog = ctk.CTkToplevel(self.root)
        loading_dialog.title("Downloading...")
        loading_dialog.geometry("300x100")
        loading_dialog.transient(self.root)
        loading_dialog.grab_set()
        
        ctk.CTkLabel(loading_dialog, text=f"Downloading {filename}...").pack(pady=20)
        
        # Start download in a separate thread
        threading.Thread(
            target=self._download_thread,
            args=(filename, loading_dialog),
            daemon=True
        ).start()
    
    def _download_thread(self, filename, loading_dialog):
        """
        Download a file in a separate thread.
        """
        success, message = self.client.download_file(filename)
        
        # Update UI in the main thread
        self.root.after(0, lambda: self._download_complete(success, message, loading_dialog))
    
    def _download_complete(self, success, message, loading_dialog):
        """
        Handle download completion.
        """
        loading_dialog.destroy()
        
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", message)
    
    def upload_file(self):
        """
        Upload a file to the server.
        """
        if not self.client.connected:
            return
        
        # Open file dialog to select a file
        file_path = filedialog.askopenfilename(title="Select a file to upload")
        
        if not file_path:
            return  # User canceled
        
        # Show a loading dialog
        loading_dialog = ctk.CTkToplevel(self.root)
        loading_dialog.title("Uploading...")
        loading_dialog.geometry("300x100")
        loading_dialog.transient(self.root)
        loading_dialog.grab_set()
        
        ctk.CTkLabel(loading_dialog, text=f"Uploading {os.path.basename(file_path)}...").pack(pady=20)
        
        # Start upload in a separate thread
        threading.Thread(
            target=self._upload_thread,
            args=(file_path, loading_dialog),
            daemon=True
        ).start()
    
    def _upload_thread(self, file_path, loading_dialog):
        """
        Upload a file in a separate thread.
        """
        success, message = self.client.upload_file(file_path)
        
        # Update UI in the main thread
        self.root.after(
            0,
            lambda: self._upload_complete(success, message, loading_dialog)
        )
    
    def _upload_complete(self, success, message, loading_dialog):
        """
        Handle upload completion.
        """
        loading_dialog.destroy()
        
        if success:
            messagebox.showinfo("Success", message)
            # Refresh file list
            self.refresh_file_list()
        else:
            messagebox.showerror("Error", message)
    
    def change_download_dir(self):
        """
        Change the download directory.
        """
        new_dir = filedialog.askdirectory(title="Select Download Directory")
        
        if new_dir:
            self.client.download_dir = new_dir
            self.download_dir_label.configure(text=f"Download Directory: {self.client.download_dir}")

def main():
    root = ctk.CTk()
    app = FileClientGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()