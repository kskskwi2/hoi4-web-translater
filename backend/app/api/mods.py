from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from ..services.mod_scanner import ModScanner

router = APIRouter()
scanner = ModScanner()

class ModRequest(BaseModel):
    workshop_path: str

@router.post("/scan")
def scan_mods(request: ModRequest):
    return scanner.scan_workshop(request.workshop_path)
