from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import Response

from app.api.dependencies import get_learning_service, get_repository, get_speech_service
from app.database.repositories import LearningRepository, VocabularyNotFoundError
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationItem,
    DashboardData,
    FrequencyUpdate,
    LanguageOption,
    PracticeSuggestion,
    ProgressStats,
    VocabularyCreate,
    VocabularyItem,
)
from app.services.ai_service import LearningService
from app.services.practice import build_practice_suggestions
from app.services.languages import language_catalog
from app.services.utf8_guard import InvalidTextError
from app.speech.service import SpeechService, SpeechServiceError


router = APIRouter(prefix="/api")


def _bad_request(error: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    payload: ChatRequest,
    service: LearningService = Depends(get_learning_service),
) -> ChatResponse:
    try:
        return await service.handle_message(payload.message, payload.language)
    except (InvalidTextError, ValueError) as error:
        raise _bad_request(error) from error


@router.get("/languages", response_model=list[LanguageOption], tags=["languages"])
async def get_languages() -> list[LanguageOption]:
    return [
        LanguageOption(
            code=profile.code,
            name=profile.name,
            native_name=profile.native_name,
            speech_code=profile.speech_code,
        )
        for profile in language_catalog()
    ]


@router.get("/vocabulary", response_model=list[VocabularyItem], tags=["vocabulary"])
async def get_vocabulary(
    limit: int = Query(default=100, ge=1, le=500),
    repository: LearningRepository = Depends(get_repository),
) -> list[VocabularyItem]:
    return repository.list_vocabulary(limit)


@router.post("/vocabulary", response_model=VocabularyItem, status_code=status.HTTP_201_CREATED, tags=["vocabulary"])
async def add_vocabulary(
    payload: VocabularyCreate,
    repository: LearningRepository = Depends(get_repository),
) -> VocabularyItem:
    try:
        return repository.add_word(
            payload.word,
            payload.meaning,
            payload.example_sentence,
            frequency=payload.frequency,
        )
    except InvalidTextError as error:
        raise _bad_request(error) from error


@router.patch("/vocabulary/{word}/frequency", response_model=VocabularyItem, tags=["vocabulary"])
async def update_vocabulary_frequency(
    word: str,
    payload: FrequencyUpdate,
    repository: LearningRepository = Depends(get_repository),
) -> VocabularyItem:
    try:
        return repository.update_frequency(word, payload.increment)
    except InvalidTextError as error:
        raise _bad_request(error) from error
    except VocabularyNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/conversations", response_model=list[ConversationItem], tags=["conversations"])
async def get_conversations(
    limit: int = Query(default=20, ge=1, le=100),
    repository: LearningRepository = Depends(get_repository),
) -> list[ConversationItem]:
    return repository.get_conversations(limit)


@router.get("/progress", response_model=ProgressStats, tags=["progress"])
async def get_progress(repository: LearningRepository = Depends(get_repository)) -> ProgressStats:
    return repository.get_progress()


@router.get("/dashboard", response_model=DashboardData, tags=["progress"])
async def get_dashboard(repository: LearningRepository = Depends(get_repository)) -> DashboardData:
    return repository.get_dashboard()


@router.get("/practice-suggestions", response_model=list[PracticeSuggestion], tags=["vocabulary"])
async def get_practice_suggestions(
    repository: LearningRepository = Depends(get_repository),
) -> list[PracticeSuggestion]:
    return build_practice_suggestions(repository.list_vocabulary(limit=3))


@router.post("/speech/transcribe", tags=["speech"])
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: str = "en",
    service: SpeechService = Depends(get_speech_service),
) -> dict[str, str]:
    if not (audio.content_type or "").startswith("audio/"):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="An audio file is required.")
    audio_content = await audio.read()
    if len(audio_content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Audio is limited to 10 MB.")
    try:
        transcript = await run_in_threadpool(service.transcribe, audio_content, language)
    except (SpeechServiceError, ValueError) as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    return {"transcript": transcript}


@router.post("/speech/synthesize", tags=["speech"])
async def synthesize_speech(
    text: str,
    language: str = "en",
    voice: str = "us",
    speed: float = Query(default=1.0, ge=0.5, le=1.5),
    service: SpeechService = Depends(get_speech_service),
) -> Response:
    try:
        audio_content = await run_in_threadpool(service.synthesize, text, language, voice, speed)
    except (InvalidTextError, ValueError) as error:
        raise _bad_request(error) from error
    except SpeechServiceError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    return Response(content=audio_content, media_type="audio/mpeg")


@router.get("/speech/status", tags=["speech"])
async def speech_status(service: SpeechService = Depends(get_speech_service)) -> dict[str, bool]:
    return {"text_to_speech": service.tts_enabled, "speech_to_text": service.stt_enabled}