#!/usr/bin/env python3
"""
Windows-compatible backend startup script
Handles signal issues that cause automatic KeyboardInterrupt
"""
import sys
import os
import signal
import asyncio
from fastapi import FastAPI
import uvicorn

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the API
from api import app

def signal_handler(signum, frame):
    """Handle signals gracefully"""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    """Start the server with Windows-compatible settings"""
    print("Starting backend server...")
    print("Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    
    # Set up signal handlers for Windows
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Use uvicorn with Windows-compatible settings
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=8000,
            log_level="info",
            access_log=True,
            loop="asyncio",
            # Windows-specific settings
            reload=False,  # Disable reload to avoid signal issues
            workers=1,     # Single worker to avoid multiprocessing issues
            # Disable signal handling that causes issues on Windows
            use_colors=True,
            server_header=False,
            date_header=False
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
