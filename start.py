import uvicorn
import webbrowser
import os
import sys

def main():
    print("Starting Paradox Localisation Manager Backend...")
    # In a real build, we might serve the frontend statics from FastAPI too
    # For dev, we assume the frontend is running separately or we just start the backend
    
    # Check if frontend build exists (to determine mode)
    frontend_dist = os.path.join(os.getcwd(), "frontend", "dist")
    
    # Just start backend for now
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8080, reload=True)

if __name__ == "__main__":
    main()
