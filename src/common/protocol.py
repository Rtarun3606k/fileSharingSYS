import json
import os
import struct

# Message types
FILE_LIST_REQUEST = 1
FILE_LIST_RESPONSE = 2
FILE_REQUEST = 3
FILE_RESPONSE = 4
FILE_UPLOAD_REQUEST = 5
FILE_UPLOAD_RESPONSE = 6
ERROR_MESSAGE = 7

# Buffer sizes
HEADER_SIZE = 8  # Size of the message header (4 bytes for type, 4 bytes for payload length)
CHUNK_SIZE = 8192  # 8KB chunks for file transfer

def create_message(msg_type, payload):
    """
    Create a message with a header and payload.
    Header format: [message type (4 bytes)][payload length (4 bytes)]
    """
    serialized_payload = json.dumps(payload).encode('utf-8') if isinstance(payload, dict) else payload
    header = struct.pack('!II', msg_type, len(serialized_payload))
    return header + serialized_payload

def parse_header(header_bytes):
    """
    Parse the header to get message type and payload length.
    """
    return struct.unpack('!II', header_bytes)

def receive_message(sock):
    """
    Receive a complete message from the socket.
    """
    # Receive the header first
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
    if msg_type in [FILE_LIST_REQUEST, FILE_LIST_RESPONSE, FILE_REQUEST, FILE_UPLOAD_REQUEST, FILE_UPLOAD_RESPONSE, ERROR_MESSAGE]:
        try:
            payload = json.loads(payload_bytes.decode('utf-8'))
        except json.JSONDecodeError:
            payload = payload_bytes
    else:
        payload = payload_bytes
    
    return msg_type, payload

def send_file_list_request(sock):
    """
    Send a request to get the list of files from the server.
    """
    message = create_message(FILE_LIST_REQUEST, {})
    sock.sendall(message)

def send_file_list_response(sock, file_list):
    """
    Send the list of files to the client.
    """
    message = create_message(FILE_LIST_RESPONSE, {'files': file_list})
    sock.sendall(message)

def send_file_request(sock, filename):
    """
    Send a request to download a file from the server.
    """
    message = create_message(FILE_REQUEST, {'filename': filename})
    sock.sendall(message)

def send_file_response(sock, filename, file_data):
    """
    Send a file to the client.
    """
    message = create_message(FILE_RESPONSE, {'filename': filename, 'file_data': file_data})
    sock.sendall(message)

def send_file_upload_request(sock, filename, file_data):
    """
    Send a request to upload a file to the server.
    """
    message = create_message(FILE_UPLOAD_REQUEST, {'filename': filename, 'file_data': file_data})
    sock.sendall(message)

def send_file_upload_response(sock, success, message=""):
    """
    Send a response after processing a file upload request.
    """
    message = create_message(FILE_UPLOAD_RESPONSE, {'success': success, 'message': message})
    sock.sendall(message)

def send_error_message(sock, error_msg):
    """
    Send an error message.
    """
    message = create_message(ERROR_MESSAGE, {'error': error_msg})
    sock.sendall(message)