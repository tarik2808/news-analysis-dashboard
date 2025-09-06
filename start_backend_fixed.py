#!/usr/bin/env python3
"""
Fixed backend startup script for Windows
"""
import sys
import os
import asyncio
from fastapi import FastAPI
import uvicorn

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the API
from api import app

def main():
    """Start the server with Windows-compatible settings"""
    print("Starting backend server...")
    print("Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    
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
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)
