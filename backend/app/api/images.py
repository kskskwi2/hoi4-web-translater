from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import os

router = APIRouter()

@router.get("/proxy")
def get_image(path: str = Query(..., description="Absolute path to the image")):
    if not os.path.exists(path) or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="Image not found or is not a file")
        
    # Basic security check: ensure we are just reading files, though for a local tool 
    # run by the user, accessing their own files is the intended behavior.
    
    return FileResponse(path)
