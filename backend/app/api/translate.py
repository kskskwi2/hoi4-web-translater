from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..services.mod_generator import ModGenerator
from ..services.mod_scanner import ModScanner
from ..services import task_manager
from ..database import get_db
from .. import models
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
    shutdown_when_complete: Optional[bool] = None  # Shutdown feature


@router.get("/ollama/models")
async def get_ollama_models(base_url: str = "http://localhost:11434"):
    """
    Fetches available Ollama models.
    """
    from ..services.translator.ollama import OllamaTranslatorService

    translator = OllamaTranslatorService(base_url=base_url)
    models = await translator.get_available_models()
    return {"models": models}


@router.get("/gemini/models")
async def get_gemini_models(
    api_key: Optional[str] = None, db: Session = Depends(get_db)
):
    """
    Fetches available Gemini models.
    """
    from ..services.translator.gemini import GeminiTranslatorService

    if not api_key:
        settings = db.query(models.Settings).first()
        if settings:
            api_key = settings.gemini_api_key

    translator = GeminiTranslatorService(api_key=api_key)
    models = await translator.get_available_models()
    return {"models": models}


@router.post("/run")
async def run_translation(
    request: TranslateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Starts the translation process in the background.
    """
    # Resolve shutdown preference
    should_shutdown = False
    if request.shutdown_when_complete is not None:
        should_shutdown = request.shutdown_when_complete
    else:
        # Fallback to DB setting
        db_settings = db.query(models.Settings).first()
        if db_settings:
            should_shutdown = db_settings.auto_shutdown or False

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

    # Create Task
    task_id = task_manager.create_task()

    # Add to background tasks
    background_tasks.add_task(
        generator.generate_translation_mod,
        source_mod=mod_info,
        output_root=request.output_path,
        task_id=task_id,
        target_lang=request.target_lang,
        service=request.service,
        service_config=service_config,
        vanilla_path=request.vanilla_path,
        glossary=request.glossary,
        shutdown_when_complete=should_shutdown,
    )

    return {
        "status": "started",
        "message": "Translation started in background",
        "task_id": task_id,
    }


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
def get_translation_status(task_id: str = None):
    """
    Returns the current translation progress.
    """
    if not task_id:
        return {"status": "idle", "percent": 0, "processed_files": 0, "total_files": 0}

    task = task_manager.get_task(task_id)
    if not task:
        # Instead of 404 (which spams logs), return a special status
        # This tells frontend "this task is gone", stop polling.
        return {
            "status": "not_found",
            "percent": 0,
            "error": "Task not found or expired",
        }

    return task
