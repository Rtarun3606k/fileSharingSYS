import socket
import base64
import os
import sys
from pathlib import Path

# Add parent directory to path for importing common module
sys.path.append(str(Path(__file__).resolve().parent.parent))
from common import protocol

class FileClient:
    def __init__(self):
        """
        Initialize the file client.
        """
        self.socket = None
        self.connected = False
        self.download_dir = os.path.join(os.path.expanduser('~'), 'Downloads')
        
        # Create download directory if it doesn't exist
        os.makedirs(self.download_dir, exist_ok=True)
    
    def connect(self, host, port):
        """
        Connect to the file server.
        
        Args:
            host: Server host address
            port: Server port
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((host, port))
            self.connected = True
            return True
        except Exception as e:
            print(f"Error connecting to server: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """
        Disconnect from the server.
        """
        if self.socket and self.connected:
            try:
                self.socket.close()
            except:
                pass
            self.connected = False
    
    def get_file_list(self):
        """
        Get the list of available files from the server.
        
        Returns:
            list: List of file information dictionaries
        """
        if not self.connected:
            return []
        
        try:
            # Send file list request
            protocol.send_file_list_request(self.socket)
            
            # Receive response
            msg_type, payload = protocol.receive_message(self.socket)
            
            if msg_type == protocol.FILE_LIST_RESPONSE:
                return payload.get('files', [])
            elif msg_type == protocol.ERROR_MESSAGE:
                print(f"Server error: {payload.get('error', 'Unknown error')}")
            else:
                print(f"Unexpected response: {msg_type}")
        
        except Exception as e:
            print(f"Error getting file list: {e}")
            self.connected = False
        
        return []
    
    def download_file(self, filename, custom_path=None):
        """
        Download a file from the server.
        
        Args:
            filename: Name of the file to download
            custom_path: Custom path to save the file to
            
        Returns:
            tuple: (success, message)
        """
        if not self.connected:
            return False, "Not connected to server"
        
        try:
            # Send file request
            protocol.send_file_request(self.socket, filename)
            
            # Receive response
            msg_type, payload = protocol.receive_message(self.socket)
            
            if msg_type == protocol.FILE_RESPONSE:
                # Get the file data
                received_filename = payload.get('filename', '')
                file_data = payload.get('file_data', '')
                
                if not received_filename or not file_data:
                    return False, "Invalid file data received"
                
                # Determine where to save the file
                save_path = custom_path if custom_path else os.path.join(self.download_dir, received_filename)
                
                # Save the file
                decoded_data = base64.b64decode(file_data)
                with open(save_path, 'wb') as file:
                    file.write(decoded_data)
                
                return True, f"File saved to {save_path}"
            
            elif msg_type == protocol.ERROR_MESSAGE:
                error_msg = payload.get('error', 'Unknown error')
                return False, f"Server error: {error_msg}"
            
            else:
                return False, "Unexpected response from server"
        
        except Exception as e:
            print(f"Error downloading file: {e}")
            self.connected = False
            return False, f"Error downloading file: {e}"
    
    def upload_file(self, file_path):
        """
        Upload a file to the server.
        
        Args:
            file_path: Path to the file to upload
            
        Returns:
            tuple: (success, message)
        """
        if not self.connected:
            return False, "Not connected to server"
        
        try:
            # Check if file exists
            if not os.path.isfile(file_path):
                return False, f"File not found: {file_path}"
            
            # Get the filename and read the file
            filename = os.path.basename(file_path)
            
            with open(file_path, 'rb') as file:
                file_data = base64.b64encode(file.read()).decode('utf-8')
            
            # Send file upload request
            protocol.send_file_upload_request(self.socket, filename, file_data)
            
            # Receive response
            msg_type, payload = protocol.receive_message(self.socket)
            
            if msg_type == protocol.FILE_UPLOAD_RESPONSE:
                success = payload.get('success', False)
                message = payload.get('message', '')
                return success, message
            
            elif msg_type == protocol.ERROR_MESSAGE:
                error_msg = payload.get('error', 'Unknown error')
                return False, f"Server error: {error_msg}"
            
            else:
                return False, "Unexpected response from server"
        
        except Exception as e:
            print(f"Error uploading file: {e}")
            self.connected = False
            return False, f"Error uploading file: {e}"