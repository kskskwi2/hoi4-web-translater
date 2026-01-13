from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from ..services.mod_generator import ModGenerator
from ..services.mod_scanner import ModScanner
import os

router = APIRouter()
generator = ModGenerator()
scanner = ModScanner()


class ServiceSettings(BaseModel):
    openai_key: Optional[str] = ""
    openai_model: Optional[str] = "gpt-4o-mini"
    claude_key: Optional[str] = ""
    claude_model: Optional[str] = "claude-3-5-sonnet-20241022"
    gemini_key: Optional[str] = ""
    gemini_model: Optional[str] = "gemini-1.5-flash"
    ollama_url: Optional[str] = "http://localhost:11434"
    ollama_model: Optional[str] = "gemma2"


class TranslateRequest(BaseModel):
    mod_path: str
    mod_name: str
    mod_id: str
    output_path: str
    service: str = "google"
    target_lang: str = "ko"
    vanilla_path: Optional[str] = None
    settings: Optional[ServiceSettings] = None
    glossary: Optional[dict] = None  # Added Glossary


@router.get("/ollama/models")
async def get_ollama_models(base_url: str = "http://localhost:11434"):
    """
    Fetches available Ollama models.
    """
    from ..services.translator.ollama import OllamaTranslatorService

    translator = OllamaTranslatorService(base_url=base_url)
    models = await translator.get_available_models()
    return {"models": models}


@router.post("/run")
async def run_translation(request: TranslateRequest, background_tasks: BackgroundTasks):
    """
    Starts the translation process in the background.
    """
    mod_info = {
        "path": request.mod_path,
        "name": request.mod_name,
        "id": request.mod_id,
        "supported_version": "1.*",
    }

    # Extract settings for the selected service
    service_config = {}
    if request.settings:
        service_config = request.settings.model_dump()

    # Reset progress
    from ..services.mod_generator import translation_progress

    translation_progress["status"] = "running"
    translation_progress["percent"] = 0
    translation_progress["processed_files"] = 0

    # Add to background tasks
    background_tasks.add_task(
        generator.generate_translation_mod,
        mod_info,
        request.output_path,
        target_lang=request.target_lang,
        service=request.service,
        service_config=service_config,
        vanilla_path=request.vanilla_path,
        glossary=request.glossary,  # Pass glossary
    )

    return {"status": "started", "message": "Translation started in background"}


@router.get("/download/{mod_id}")
def download_mod(mod_id: str, zip_path: str):
    """
    Downloads the zipped mod file.
    """
    if not os.path.exists(zip_path) or not os.path.isfile(zip_path):
        raise HTTPException(status_code=404, detail="Zip file not found")

    return FileResponse(
        zip_path, media_type="application/zip", filename=os.path.basename(zip_path)
    )


@router.post("/zip")
def create_zip_endpoint(path: str, name: str):
    """
    Trigger zip creation manually if needed or as part of flow.
    """
    try:
        archive = generator.create_zip(path, name)
        return {"zip_path": archive}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def get_translation_status():
    """
    Returns the current translation progress.
    """
    from ..services.mod_generator import translation_progress

    return translation_progress
