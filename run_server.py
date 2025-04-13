#!/usr/bin/env python3
import argparse
import os
import sys
from src.server.server import FileServer

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Secure File Sharing Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9000, help="Port to listen on (default: 9000)")
    parser.add_argument("--storage", default="storage", help="Directory to store files (default: storage)")
    
    args = parser.parse_args()
    
    # Create and start the server
    server = FileServer(args.host, args.port, args.storage)
    
    try:
        print("Starting server...")
        server.start()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        server.stop()

if __name__ == "__main__":
    main()