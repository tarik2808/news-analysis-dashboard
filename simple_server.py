#!/usr/bin/env python3
"""
Simple test server to verify uvicorn works
"""
from fastapi import FastAPI
import uvicorn

# Create a simple FastAPI app
app = FastAPI(title="Simple Test API")

@app.get("/")
def read_root():
    return {"message": "Hello World", "status": "running"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "server": "uvicorn"}

if __name__ == "__main__":
    print("Starting simple test server...")
    print("Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop")
    
    try:
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=8000, 
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
