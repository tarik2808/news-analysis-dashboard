#!/usr/bin/env python3
"""
Start script for the News Analysis Platform
Starts both the FastAPI backend and React frontend
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting FastAPI backend...")
    try:
        # Start the backend server
        backend_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", "api:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ], cwd=Path(__file__).parent)
        return backend_process
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start the React frontend development server"""
    print("🎨 Starting React frontend...")
    try:
        # Change to frontend directory and start React
        frontend_dir = Path(__file__).parent / "frontend"
        # Use full path to npm since it's not in PATH
        npm_path = r"C:\Program Files\nodejs\npm.cmd"
        frontend_process = subprocess.Popen([
            npm_path, "start"
        ], cwd=frontend_dir)
        return frontend_process
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def main():
    """Main function to start both servers"""
    print("📰 News Analysis Platform - Starting...")
    print("=" * 50)
    
    # Check if required files exist
    if not Path("api.py").exists():
        print("❌ api.py not found. Make sure you're in the project root directory.")
        return
    
    if not Path("frontend/package.json").exists():
        print("❌ frontend/package.json not found. Make sure the frontend is set up.")
        return
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        return
    
    # Wait a moment for backend to start
    time.sleep(3)
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        print("❌ Frontend failed to start. Stopping backend...")
        backend_process.terminate()
        return
    
    print("=" * 50)
    print("✅ Both servers started successfully!")
    print("📊 Backend API: http://localhost:8000")
    print("🌐 Frontend: http://localhost:3000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 50)
    print("Press Ctrl+C to stop both servers")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
            # Check if processes are still running
            if backend_process.poll() is not None:
                print("❌ Backend server stopped unexpectedly")
                break
            if frontend_process.poll() is not None:
                print("❌ Frontend server stopped unexpectedly")
                break
    except KeyboardInterrupt:
        print("\n🛑 Stopping servers...")
    finally:
        # Clean up processes
        if backend_process:
            backend_process.terminate()
            print("✅ Backend stopped")
        if frontend_process:
            frontend_process.terminate()
            print("✅ Frontend stopped")
        print("👋 Goodbye!")

if __name__ == "__main__":
    main() 