import json
import os
import struct
import base64  # Added missing import

# Message types
FILE_LIST_REQUEST = 1
FILE_LIST_RESPONSE = 2
FILE_REQUEST = 3
FILE_RESPONSE = 4
FILE_UPLOAD_REQUEST = 5
FILE_UPLOAD_RESPONSE = 6
ERROR_MESSAGE = 7
FILE_CHUNK = 8
FILE_CHUNK_ACK = 9
FILE_TRANSFER_COMPLETE = 10

# Buffer sizes
HEADER_SIZE = 8
CHUNK_SIZE = 8192
MAX_CHUNK_SIZE = 65536

def create_message(msg_type, payload):
    """Create a message with header and payload"""
    if isinstance(payload, dict):
        serialized_payload = json.dumps(payload).encode('utf-8')
    else:
        serialized_payload = payload
    header = struct.pack('!II', msg_type, len(serialized_payload))
    return header + serialized_payload

def parse_header(header_bytes):
    """Parse the header to get message type and payload length"""
    return struct.unpack('!II', header_bytes)

def receive_message(sock):
    """Receive a complete message from the socket"""
    # Receive the header first
    try:
        header_bytes = sock.recv(HEADER_SIZE)
        if not header_bytes or len(header_bytes) < HEADER_SIZE:
            return None, None
        
        # Parse the header
        msg_type, payload_length = parse_header(header_bytes)
        
        # Receive the payload
        payload_bytes = b''
        remaining = payload_length
        
        while remaining > 0:
            chunk = sock.recv(min(remaining, CHUNK_SIZE))
            if not chunk:
                return None, None
            payload_bytes += chunk
            remaining -= len(chunk)
        
        # Parse the payload based on message type
        if msg_type in [FILE_LIST_REQUEST, FILE_LIST_RESPONSE, FILE_REQUEST, 
                       FILE_UPLOAD_RESPONSE, ERROR_MESSAGE,
                       FILE_CHUNK_ACK, FILE_TRANSFER_COMPLETE]:
            # These should be JSON
            try:
                return msg_type, json.loads(payload_bytes.decode('utf-8'))
            except:
                # If JSON parsing fails, return an empty dict
                return msg_type, {}
        
        elif msg_type == FILE_CHUNK:
            # Special handling for file chunks
            try:
                # Try to decode as JSON first
                payload = json.loads(payload_bytes.decode('utf-8'))
                return msg_type, payload
            except:
                # If it fails, it's probably binary data - create a safe dict
                return msg_type, {"chunk_id": 0, "total_chunks": 1, "data": ""}
        
        elif msg_type == FILE_UPLOAD_REQUEST:
            # Special handling for file uploads which might have binary data
            try:
                return msg_type, json.loads(payload_bytes.decode('utf-8'))
            except:
                return msg_type, {"filename": "", "file_data": ""}
        
        elif msg_type == FILE_RESPONSE:
            # File response metadata
            try:
                return msg_type, json.loads(payload_bytes.decode('utf-8'))
            except:
                return msg_type, {"filename": "", "file_size": 0, "chunks": 0}
        
        else:
            # For unknown types, just return the raw bytes
            return msg_type, payload_bytes
            
    except Exception as e:
        print(f"Error in receive_message: {e}")
        return None, None

# Message sending functions
def send_file_list_request(sock):
    """Send a request to get the list of files from the server"""
    message = create_message(FILE_LIST_REQUEST, {})
    sock.sendall(message)

def send_file_list_response(sock, file_list):
    """Send the list of files to the client"""
    message = create_message(FILE_LIST_RESPONSE, {'files': file_list})
    sock.sendall(message)

def send_file_request(sock, filename):
    """Send a request to download a file from the server"""
    message = create_message(FILE_REQUEST, {'filename': filename})
    sock.sendall(message)

def send_file_response(sock, filename, file_size):
    """Send file metadata as a response to a download request"""
    total_chunks = (file_size // MAX_CHUNK_SIZE) + (1 if file_size % MAX_CHUNK_SIZE > 0 else 0)
    message = create_message(FILE_RESPONSE, {
        'filename': filename,
        'file_size': file_size,
        'chunks': total_chunks
    })
    sock.sendall(message)

def send_file_chunk(sock, chunk_id, total_chunks, data):
    """Send a chunk of file data"""
    # Ensure data is properly encoded as string if it's binary
    if isinstance(data, bytes):
        data = base64.b64encode(data).decode('utf-8')
        
    message = create_message(FILE_CHUNK, {
        'chunk_id': chunk_id,
        'total_chunks': total_chunks,
        'data': data
    })
    sock.sendall(message)

def send_chunk_ack(sock, chunk_id):
    """Send acknowledgment for a received chunk"""
    message = create_message(FILE_CHUNK_ACK, {'chunk_id': chunk_id})
    sock.sendall(message)

def send_transfer_complete(sock, success, filename=""):
    """Signal that a file transfer is complete"""
    message = create_message(FILE_TRANSFER_COMPLETE, {
        'success': success,
        'filename': filename
    })
    sock.sendall(message)

def send_file_upload_request(sock, filename, file_data):
    """Send a request to upload a file to the server"""
    message = create_message(FILE_UPLOAD_REQUEST, {'filename': filename, 'file_data': file_data})
    sock.sendall(message)

def send_file_upload_response(sock, success, message=""):
    """Send a response after processing a file upload request"""
    message = create_message(FILE_UPLOAD_RESPONSE, {'success': success, 'message': message})
    sock.sendall(message)

def send_error_message(sock, error_msg):
    """Send an error message"""
    message = create_message(ERROR_MESSAGE, {'error': error_msg})
    sock.sendall(message)