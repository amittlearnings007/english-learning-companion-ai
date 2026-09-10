from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True, slots=True)
class Settings:
    """Configuration loaded from the local .env file."""

    app_name: str = os.getenv("APP_NAME", "English Learning Companion AI")
    environment: str = os.getenv("APP_ENV", "development")
    database_path: Path = PROJECT_ROOT / os.getenv("DATABASE_PATH", "data/vocabulary.db")
    llm_provider: str = os.getenv("LLM_PROVIDER", "rule_based")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    tts_enabled: bool = os.getenv("TTS_ENABLED", "true").lower() == "true"
    stt_enabled: bool = os.getenv("STT_ENABLED", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    allowed_origins: tuple[str, ...] = tuple(
        origin.strip()
        for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:8501,http://127.0.0.1:8501").split(",")
        if origin.strip()
    )


settings = Settings()