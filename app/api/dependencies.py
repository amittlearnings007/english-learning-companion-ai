from __future__ import annotations

from typing import cast

from fastapi import Request

from app.database.repositories import LearningRepository
from app.services.ai_service import LearningService
from app.speech.service import SpeechService


def get_learning_service(request: Request) -> LearningService:
    return cast(LearningService, request.app.state.learning_service)


def get_repository(request: Request) -> LearningRepository:
    return cast(LearningRepository, request.app.state.repository)


def get_speech_service(request: Request) -> SpeechService:
    return cast(SpeechService, request.app.state.speech_service)