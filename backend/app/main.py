from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI(title="Paradox Localisation Manager")

# CORS setup for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.app.api import mods, images, translate

app.include_router(mods.router, prefix="/api/mods", tags=["mods"])
app.include_router(images.router, prefix="/api/images", tags=["images"])
app.include_router(translate.router, prefix="/api/translate", tags=["translate"])

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount static files
frontend_dist = os.path.join(os.getcwd(), "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount(
        "/assets",
        StaticFiles(directory=os.path.join(frontend_dist, "assets")),
        name="assets",
    )


@app.get("/")
def read_root():
    if os.path.exists(frontend_dist):
        return FileResponse(os.path.join(frontend_dist, "index.html"))
    return {"status": "ok", "message": "Backend Running (Frontend not found)"}


@app.get("/api/config")
def get_default_paths():
    import ctypes.wintypes
    import pathlib
    import subprocess

    CSIDL_PERSONAL = 5
    SHGFP_TYPE_CURRENT = 0

    documents_root = None
    try:
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(
            None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf
        )
        documents_root = buf.value
    except Exception:
        documents_root = os.path.expanduser("~")

    # Paradox specific path - FORCE OneDrive if that's what was detected
    documents = os.path.join(
        documents_root, "Paradox Interactive", "Hearts of Iron IV", "mod"
    )
    final_documents_path = documents

    # Try to create the directory using subprocess (more reliable for OneDrive)
    try:
        # Use cmd.exe to create directory - bypasses Python's file handling issues
        subprocess.run(
            f'mkdir "{documents}"', shell=True, check=False, capture_output=True
        )

        # Verify it exists now
        if os.path.exists(documents):
            print(f"SUCCESS: Created/Verified path via subprocess: {documents}")
        else:
            # Try pathlib as fallback
            pathlib.Path(documents).mkdir(parents=True, exist_ok=True)

        # Final write test
        test_file = os.path.join(documents, ".write_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print(f"Verified write access to: {documents}")
    except Exception as e:
        print(
            f"Warning: Path access issue ({e}). Using as-is, generator will handle fallback."
        )

    # Try to find Steam Workshop path
    workshop_paths = [
        r"C:\Program Files (x86)\Steam\steamapps\workshop\content\394360",
        r"D:\SteamLibrary\steamapps\workshop\content\394360",
        r"E:\SteamLibrary\steamapps\workshop\content\394360",
        r"F:\SteamLibrary\steamapps\workshop\content\394360",
        os.path.expanduser(r"~\SteamLibrary\steamapps\workshop\content\394360"),
    ]

    steam_workshop = ""
    for path in workshop_paths:
        if os.path.exists(path):
            steam_workshop = path
            break

    # Fallback to standard if not found (even if it doesn't exist, to show something)
    if not steam_workshop:
        steam_workshop = (
            r"C:\Program Files (x86)\Steam\steamapps\workshop\content\394360"
        )

    return {"documents_path": final_documents_path, "workshop_path": steam_workshop}


@app.get("/api/test-path")
def test_path_write():
    """Debug endpoint to test OneDrive path access"""
    import ctypes.wintypes
    import subprocess

    CSIDL_PERSONAL = 5
    buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_PERSONAL, None, 0, buf)
    docs = buf.value

    target = os.path.join(docs, "Paradox Interactive", "Hearts of Iron IV", "mod")
    results = []

    # Test 1: Does base docs exist?
    results.append(f"Documents root exists: {os.path.exists(docs)}")

    # Test 2: Try mkdir via subprocess
    try:
        cmd = f'mkdir "{target}"'
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        results.append(f"mkdir result: {proc.returncode}, stderr: {proc.stderr}")
    except Exception as e:
        results.append(f"mkdir failed: {e}")

    # Test 3: Does target exist now?
    results.append(f"Target exists after mkdir: {os.path.exists(target)}")

    # Test 4: Try write
    test_file = os.path.join(target, ".api_test")
    try:
        with open(test_file, "w") as f:
            f.write("api test")
        results.append(f"Write SUCCESS")
        os.remove(test_file)
    except Exception as e:
        results.append(f"Write FAILED: {e}")

    return {"target": target, "results": results}


if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
