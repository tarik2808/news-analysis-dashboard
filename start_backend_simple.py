#!/usr/bin/env python3
"""
Ultra-simple backend startup for Windows
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the API
from api import app

if __name__ == "__main__":
    print("Starting backend server...")
    print("Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop the server")
    
    # Use the simplest possible uvicorn call
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
