import os
import socket
import threading
import base64
import sys
from pathlib import Path

# Add parent directory to path for importing common module
sys.path.append(str(Path(__file__).resolve().parent.parent))
from common import protocol

class FileServer:
    def __init__(self, host='0.0.0.0', port=9000, storage_dir='storage'):
        """
        Initialize the file server.
        
        Args:
            host: Host address to bind to
            port: Port to listen on
            storage_dir: Directory where files are stored
        """
        self.host = host
        self.port = port
        self.storage_dir = storage_dir
        self.socket = None
        self.clients = []
        self.running = False
        
        # Create storage directory if it doesn't exist
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def start(self):
        """
        Start the file server.
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            print(f"Server started on {self.host}:{self.port}")
            print(f"Files will be stored in: {os.path.abspath(self.storage_dir)}")
            
            self.accept_connections()
        except Exception as e:
            print(f"Error starting server: {e}")
    
    def stop(self):
        """
        Stop the file server.
        """
        self.running = False
        if self.socket:
            self.socket.close()
        
        for client in self.clients:
            try:
                client.close()
            except:
                pass
        
        print("Server stopped")
    
    def accept_connections(self):
        """
        Accept incoming client connections.
        """
        while self.running:
            try:
                client_socket, address = self.socket.accept()
                print(f"New connection from {address[0]}:{address[1]}")
                
                # Start a new thread to handle this client
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                client_thread.start()
                self.clients.append(client_socket)
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
                break
    
    def handle_client(self, client_socket, address):
        """
        Handle communication with a client.
        
        Args:
            client_socket: Socket connected to the client
            address: Client's address
        """
        try:
            while self.running:
                # Receive a message from the client
                msg_type, payload = protocol.receive_message(client_socket)
                
                if msg_type is None:
                    # Connection closed
                    break
                
                # Process the message based on its type
                if msg_type == protocol.FILE_LIST_REQUEST:
                    self.handle_file_list_request(client_socket)
                
                elif msg_type == protocol.FILE_REQUEST:
                    self.handle_file_request(client_socket, payload)
                
                elif msg_type == protocol.FILE_UPLOAD_REQUEST:
                    self.handle_file_upload_request(client_socket, payload)
                
                else:
                    print(f"Received unknown message type: {msg_type}")
        
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        
        finally:
            # Clean up
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            
            try:
                client_socket.close()
            except:
                pass
            
            print(f"Connection closed with {address[0]}:{address[1]}")
    
    def handle_file_list_request(self, client_socket):
        """
        Handle a request for the list of available files.
        
        Args:
            client_socket: Socket connected to the client
        """
        try:
            # Get the list of files in the storage directory
            file_list = []
            for filename in os.listdir(self.storage_dir):
                file_path = os.path.join(self.storage_dir, filename)
                if os.path.isfile(file_path):
                    # Add file information
                    size = os.path.getsize(file_path)
                    file_list.append({
                        'name': filename,
                        'size': size,
                        'size_formatted': self.format_size(size)
                    })
            
            # Send the file list to the client
            protocol.send_file_list_response(client_socket, file_list)
            print(f"Sent list of {len(file_list)} files to client")
        
        except Exception as e:
            print(f"Error handling file list request: {e}")
            protocol.send_error_message(client_socket, str(e))
    
    def handle_file_request(self, client_socket, payload):
        """
        Handle a request to download a file.
        
        Args:
            client_socket: Socket connected to the client
            payload: Message payload containing the filename
        """
        try:
            filename = payload.get('filename', '')
            file_path = os.path.join(self.storage_dir, filename)
            
            if not os.path.isfile(file_path):
                protocol.send_error_message(client_socket, f"File not found: {filename}")
                return
            
            # Read the file and encode it
            with open(file_path, 'rb') as file:
                file_data = base64.b64encode(file.read()).decode('utf-8')
            
            # Send the file to the client
            protocol.send_file_response(client_socket, filename, file_data)
            print(f"Sent file: {filename}")
        
        except Exception as e:
            print(f"Error handling file request: {e}")
            protocol.send_error_message(client_socket, str(e))
    
    def handle_file_upload_request(self, client_socket, payload):
        """
        Handle a request to upload a file.
        
        Args:
            client_socket: Socket connected to the client
            payload: Message payload containing the filename and file data
        """
        try:
            filename = payload.get('filename', '')
            file_data = payload.get('file_data', '')
            
            if not filename or not file_data:
                protocol.send_error_message(client_socket, "Invalid file upload request")
                return
            
            # Ensure the filename is safe
            filename = os.path.basename(filename)
            file_path = os.path.join(self.storage_dir, filename)
            
            # Decode and write the file
            decoded_data = base64.b64decode(file_data)
            with open(file_path, 'wb') as file:
                file.write(decoded_data)
            
            # Send a success response
            protocol.send_file_upload_response(client_socket, True, f"File {filename} uploaded successfully")
            print(f"Received file: {filename}")
        
        except Exception as e:
            print(f"Error handling file upload request: {e}")
            protocol.send_error_message(client_socket, str(e))
    
    @staticmethod
    def format_size(size):
        """
        Format a file size in bytes to a human-readable string.
        
        Args:
            size: Size in bytes
            
        Returns:
            Formatted size string
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} PB"

def main():
    server = FileServer()
    try:
        server.start()
    except KeyboardInterrupt:
        print("Shutting down server...")
    finally:
        server.stop()

if __name__ == "__main__":
    main()