from __future__ import annotations

import json
import logging
import re
from collections.abc import Sequence
from typing import Protocol

import httpx

from app.config import Settings, settings
from app.database.repositories import LearningRepository
from app.models.schemas import ChatResponse, ConversationItem, Correction, VocabularyCandidate
from app.prompts.coach import build_system_prompt
from app.services.utf8_guard import validate_utf8_text
from app.services.vocabulary import extract_vocabulary
from app.services.languages import get_language


logger = logging.getLogger(__name__)


class CoachResult(Protocol):
    reply: str
    correction: Correction | None
    vocabulary: list[VocabularyCandidate]


class CoachOutput:
    """Validated internal representation returned by any coaching provider."""

    def __init__(
        self,
        reply: str,
        correction: Correction | None = None,
        vocabulary: list[VocabularyCandidate] | None = None,
    ) -> None:
        self.reply = validate_utf8_text(reply, "AI reply")
        self.correction = correction
        self.vocabulary = vocabulary or []


class LanguageCoach(Protocol):
    async def respond(self, message: str, history: Sequence[ConversationItem], language: str = "en") -> CoachOutput: ...


class RuleBasedCoach:
    """Reliable, child-friendly local coach that follows the one-correction rule."""

    _corrections: tuple[tuple[re.Pattern[str], str, str, str], ...] = (
        (
            re.compile(r"yesterday i go to market and buy some fruits", re.IGNORECASE),
            "Yesterday I go to market and buy some fruits.",
            "Yesterday I went to the market and bought some fruits.",
            "For actions completed in the past, use 'went' and 'bought'.",
        ),
        (
            re.compile(r"\bi am agree\b", re.IGNORECASE),
            "I am agree",
            "I agree",
            "Say 'agree' by itself.",
        ),
        (
            re.compile(r"\bpeople is\b", re.IGNORECASE),
            "people is",
            "people are",
            "Say 'people are'.",
        ),
        (
            re.compile(r"\bmore better\b", re.IGNORECASE),
            "more better",
            "better",
            "'Better' is enough.",
        ),
        (
            re.compile(r"\bi goed\b", re.IGNORECASE),
            "I goed",
            "I went",
            "Say 'went' for yesterday.",
        ),
        (
            re.compile(r"\btwo foot\b", re.IGNORECASE),
            "two foot",
            "two feet",
            "Say 'feet' for two.",
        ),
        (
            re.compile(r"\bhe go\b", re.IGNORECASE),
            "he go",
            "he goes",
            "Say 'he goes'.",
        ),
    )

    async def respond(self, message: str, history: Sequence[ConversationItem], language: str = "en") -> CoachOutput:
        del history
        correction = self._find_single_correction(message)
        return CoachOutput(
            reply=self._conversation_reply(message, language),
            correction=correction,
            vocabulary=extract_vocabulary(message),
        )

    def _find_single_correction(self, message: str) -> Correction | None:
        for pattern, original, corrected, reason in self._corrections:
            if pattern.search(message):
                return Correction(original=original, corrected=corrected, reason=reason)
        return None

    @staticmethod
    def _conversation_reply(message: str, language: str = "en") -> str:
        normalized = message.lower()
        if language != "en":
            localized_replies = {
                "es": "¡Hola, amigo! ¿Qué ves?",
                "fr": "Bonjour, mon ami ! Qu'est-ce que tu vois ?",
                "de": "Hallo, Freund! Was siehst du?",
                "it": "Ciao, amico! Che cosa vedi?",
                "pt": "Olá, amigo! O que você vê?",
                "hi": "नमस्ते दोस्त! तुम क्या देखते हो?",
                "bn": "হ্যালো বন্ধু! তুমি কী দেখছ?",
                "ja": "こんにちは、おともだち！なにが見える？",
                "ko": "안녕, 친구야! 무엇이 보여?",
                "ar": "مرحبا يا صديقي! ماذا ترى؟",
                "zh-CN": "你好，朋友！你看到了什么？",
                "ru": "Привет, друг! Что ты видишь?",
            }
            return localized_replies.get(language, f"Hello, friend! Let's play in {get_language(language).name}.")
        if "fruit" in normalized or "market" in normalized:
            return "Yummy! Which fruit do you like?"
        if "color" in normalized or "colour" in normalized:
            return "Colors are fun! What color do you see?"
        if any(animal in normalized for animal in ("cat", "dog", "bird", "lion")):
            return "I like animals! Can you make that animal sound?"
        if "play" in normalized or "toy" in normalized or "ball" in normalized:
            return "That sounds fun! What are you playing with?"
        if "happy" in normalized or "sad" in normalized:
            return "Thank you for telling me. Can you show me with your face?"
        if "weekend" in normalized:
            return "What a fun day! What did you play?"
        if "work" in normalized or "study" in normalized:
            return "Good talking! What did you see?"
        if "astronomy" in normalized:
            return "Wow, space! Can you point to the moon?"
        if "hello" in normalized or "hi" in normalized:
            return "Hello, friend! Can you say hi with a wave?"
        return "Great talking! What do you see?"


class OpenAICompatibleCoach:
    """Coach for OpenAI, GitHub Models, Azure-compatible, and similar chat APIs."""

    def __init__(self, configuration: Settings) -> None:
        self.api_key = configuration.openai_api_key
        self.base_url = configuration.openai_base_url.rstrip("/")
        self.model = configuration.openai_model

    async def respond(
        self,
        message: str,
        history: Sequence[ConversationItem],
        language: str = "en",
    ) -> CoachOutput:
        profile = get_language(language)
        messages = [{"role": "system", "content": build_system_prompt(profile.name, profile.code)}]
        for conversation in reversed(history[-6:]):
            messages.extend(
                [
                    {"role": "user", "content": conversation.user_message},
                    {"role": "assistant", "content": conversation.ai_response},
                ]
            )
        messages.append({"role": "user", "content": message})
        response_payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 450,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=response_payload,
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(self._strip_code_fence(content))
        correction_data = parsed.get("correction")
        correction = Correction.model_validate(correction_data) if correction_data else None
        vocabulary = [VocabularyCandidate.model_validate(item) for item in parsed.get("vocabulary", [])[:2]]
        return CoachOutput(reply=parsed["reply"], correction=correction, vocabulary=vocabulary)

    @staticmethod
    def _strip_code_fence(content: str) -> str:
        return content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()


class ResilientCoach:
    """Use a local coach when a configured remote model is temporarily unavailable."""

    def __init__(self, primary: LanguageCoach, fallback: LanguageCoach) -> None:
        self.primary = primary
        self.fallback = fallback

    async def respond(self, message: str, history: Sequence[ConversationItem], language: str = "en") -> CoachOutput:
        try:
            return await self.primary.respond(message, history, language)
        except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            logger.warning("Remote AI response failed; using local coaching: %s", error)
            return await self.fallback.respond(message, history, language)


def build_coach(configuration: Settings = settings) -> LanguageCoach:
    local_coach = RuleBasedCoach()
    provider = configuration.llm_provider.lower()
    if provider in {"openai", "openai_compatible", "github_models", "azure_openai"} and configuration.openai_api_key:
        return ResilientCoach(OpenAICompatibleCoach(configuration), local_coach)
    return local_coach


class LearningService:
    """Coordinates coaching, vocabulary extraction, and transactional persistence."""

    def __init__(self, repository: LearningRepository, coach: LanguageCoach) -> None:
        self.repository = repository
        self.coach = coach

    async def handle_message(self, message: str, language: str = "en") -> ChatResponse:
        validated_message = validate_utf8_text(message, "message")
        profile = get_language(language)
        history = self.repository.get_conversations(limit=6)
        result = await self.coach.respond(validated_message, history, profile.code)
        vocabulary = result.vocabulary or extract_vocabulary(validated_message)
        conversation_id, stored_vocabulary = self.repository.save_turn(
            user_message=validated_message,
            ai_response=result.reply,
            correction=result.correction,
            vocabulary=vocabulary,
        )
        return ChatResponse(
            reply=result.reply,
            correction=result.correction,
            vocabulary=stored_vocabulary,
            conversation_id=conversation_id,
            language=profile.code,
        )