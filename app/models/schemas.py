from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class Correction(BaseModel):
    original: str = Field(min_length=1, max_length=2_000)
    corrected: str = Field(min_length=1, max_length=2_000)
    reason: str = Field(min_length=1, max_length=500)


class VocabularyCandidate(BaseModel):
    word: str = Field(min_length=1, max_length=80)
    meaning: str = Field(min_length=1, max_length=300)
    example_sentence: str = Field(min_length=1, max_length=500)


class VocabularyItem(VocabularyCandidate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    learned_date: datetime
    frequency: int


class ConversationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_message: str
    ai_response: str
    correction: str | None
    timestamp: datetime


class ProgressStats(BaseModel):
    total_messages: int
    corrections_given: int
    vocabulary_count: int
    last_updated: datetime


class ActivityPoint(BaseModel):
    date: str
    count: int


class PracticeSuggestion(BaseModel):
    word: str
    prompt: str
    focus: str


class LanguageOption(BaseModel):
    code: str
    name: str
    native_name: str
    speech_code: str


class DashboardData(BaseModel):
    progress: ProgressStats
    most_used_words: list[VocabularyItem]
    daily_activity: list[ActivityPoint]
    new_words_per_week: list[ActivityPoint]
    corrections_by_date: list[ActivityPoint]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)
    language: str = Field(default="en", min_length=2, max_length=20)


class ChatResponse(BaseModel):
    reply: str
    correction: Correction | None
    vocabulary: list[VocabularyItem]
    conversation_id: int
    language: str


class VocabularyCreate(VocabularyCandidate):
    frequency: int = Field(default=1, ge=0, le=10_000)


class FrequencyUpdate(BaseModel):
    increment: int = Field(default=1, ge=1, le=1_000)