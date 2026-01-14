from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db, engine
from .. import models

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

router = APIRouter()


class SettingsSchema(BaseModel):
    steam_workshop_path: Optional[str] = None
    hoi4_documents_path: Optional[str] = None
    vanilla_path: Optional[str] = None
    openai_api_key: Optional[str] = None
    openai_model: Optional[str] = "gpt-4o-mini"
    claude_api_key: Optional[str] = None
    claude_model: Optional[str] = "claude-3-5-sonnet-20241022"
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = "gemini-1.5-flash"
    deepseek_api_key: Optional[str] = None
    paratranz_token: Optional[str] = None
    paratranz_project_id: Optional[int] = None
    enable_paratranz: Optional[bool] = False
    auto_upload_paratranz: Optional[bool] = False
    glossary: Optional[str] = "{}"  # JSON string
    ollama_url: Optional[str] = "http://localhost:11434"
    ollama_model: Optional[str] = "gemma2"
    source_language: Optional[str] = "en"
    target_language: Optional[str] = "ko"
    theme_mode: Optional[str] = "dark"
    auto_shutdown: Optional[bool] = False

    class Config:
        from_attributes = True


@router.get("/", response_model=SettingsSchema)
def get_settings(db: Session = Depends(get_db)):
    settings = db.query(models.Settings).first()
    if not settings:
        # Create default
        settings = models.Settings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.post("/", response_model=SettingsSchema)
def update_settings(settings_in: SettingsSchema, db: Session = Depends(get_db)):
    settings = db.query(models.Settings).first()
    if not settings:
        settings = models.Settings()
        db.add(settings)

    # Update fields
    for var, value in settings_in.dict(exclude_unset=True).items():
        setattr(settings, var, value)

    db.commit()
    db.refresh(settings)
    return settings
