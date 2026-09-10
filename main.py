from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import Utf8WriteValidationMiddleware
from app.api.routes import router as api_router
from app.config import settings
from app.database.repositories import LearningRepository
from app.logging_config import configure_logging
from app.services.ai_service import LanguageCoach, LearningService, build_coach
from app.speech.service import SpeechService


def create_app(*, database_path: Path | None = None, coach: LanguageCoach | None = None) -> FastAPI:
    """Build the API with replaceable dependencies for tests and deployments."""
    repository = LearningRepository(database_path)
    learning_service = LearningService(repository, coach or build_coach())
    speech_service = SpeechService()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        repository.initialize()
        application.state.repository = repository
        application.state.learning_service = learning_service
        application.state.speech_service = speech_service
        yield

    application = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(Utf8WriteValidationMiddleware)
    application.include_router(api_router)

    @application.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    return application


configure_logging()
app = create_app()