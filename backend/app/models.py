from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from .database import Base


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)

    # Paths
    steam_workshop_path = Column(String(512), nullable=True)
    hoi4_documents_path = Column(String(512), nullable=True)
    vanilla_path = Column(String(512), nullable=True)

    # API Keys & Models
    openai_api_key = Column(String(255), nullable=True)
    openai_model = Column(String(255), default="gpt-4o-mini")

    claude_api_key = Column(String(255), nullable=True)
    claude_model = Column(String(255), default="claude-3-5-sonnet-20241022")

    gemini_api_key = Column(String(255), nullable=True)
    gemini_model = Column(String(255), default="gemini-1.5-flash")

    deepseek_api_key = Column(String(255), nullable=True)

    # Paratranz
    paratranz_token = Column(String(255), nullable=True)
    paratranz_project_id = Column(Integer, nullable=True)
    enable_paratranz = Column(Boolean, default=False)
    auto_upload_paratranz = Column(Boolean, default=False)  # New setting

    # Glossary (JSON stored as Text)
    glossary = Column(Text, default="{}")

    # Ollama
    ollama_url = Column(String(255), default="http://localhost:11434")
    ollama_model = Column(String(255), default="gemma2")

    # Preferences
    source_language = Column(String(10), default="en")
    target_language = Column(String(10), default="ko")
    theme_mode = Column(String(20), default="dark")
    auto_shutdown = Column(Boolean, default=False)

    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), default=func.now()
    )


class TranslationTask(Base):
    __tablename__ = "translation_tasks"

    id = Column(String(36), primary_key=True)  # UUID
    mod_name = Column(String(255))
    status = Column(String(50))
    progress = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
