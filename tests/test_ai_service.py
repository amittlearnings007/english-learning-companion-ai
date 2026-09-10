from __future__ import annotations

import asyncio
import json

import httpx

from app.config import Settings
from app.services.ai_service import (
    LearningService,
    OpenAICompatibleCoach,
    ResilientCoach,
    RuleBasedCoach,
    build_coach,
)


def test_rule_based_coach_corrects_only_one_item() -> None:
    result = asyncio.run(RuleBasedCoach().respond("Yesterday I go to market and buy some fruits.", []))

    assert result.reply == "Yummy! Which fruit do you like?"
    assert result.correction is not None
    assert result.correction.corrected == "Yesterday I went to the market and bought some fruits."


def test_rule_based_coach_uses_playful_age_appropriate_language() -> None:
    result = asyncio.run(RuleBasedCoach().respond("I goed to the park with my red ball.", []))

    assert result.reply == "That sounds fun! What are you playing with?"
    assert result.correction is not None
    assert result.correction.corrected == "I went"
    assert result.correction.reason == "Say 'went' for yesterday."


def test_learning_service_extracts_and_tracks_vocabulary(repository) -> None:
    service = LearningService(repository, RuleBasedCoach())
    response = asyncio.run(service.handle_message("I am fascinated by astronomy."))

    assert response.correction is None
    assert {word.word for word in response.vocabulary} == {"fascinated", "astronomy"}
    assert repository.get_progress().vocabulary_count == 2


def test_openai_compatible_coach_parses_structured_response(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "reply": "That sounds interesting. What did you enjoy most?",
                                    "correction": {
                                        "original": "I am agree",
                                        "corrected": "I agree",
                                        "reason": "Use agree as a verb.",
                                    },
                                    "vocabulary": [
                                        {
                                            "word": "interesting",
                                            "meaning": "making you want to know more",
                                            "example_sentence": "It was an interesting lesson.",
                                        }
                                    ],
                                }
                            )
                        }
                    }
                ]
            }

    class FakeClient:
        request: dict | None = None

        def __init__(self, **_: object) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_: object) -> None:
            return None

        async def post(self, _: str, **kwargs: object) -> FakeResponse:
            FakeClient.request = kwargs
            return FakeResponse()

    monkeypatch.setattr("app.services.ai_service.httpx.AsyncClient", FakeClient)
    configuration = Settings(
        llm_provider="openai",
        openai_api_key="test-key",
        openai_base_url="https://models.example/v1",
        openai_model="test-model",
    )

    result = asyncio.run(OpenAICompatibleCoach(configuration).respond("I am agree.", [], "es"))

    assert result.correction is not None
    assert result.correction.corrected == "I agree"
    assert result.vocabulary[0].word == "interesting"
    assert FakeClient.request is not None
    assert FakeClient.request["json"]["model"] == "test-model"
    assert "Spanish" in FakeClient.request["json"]["messages"][0]["content"]


def test_resilient_coach_falls_back_when_remote_provider_fails() -> None:
    class UnavailableCoach:
        async def respond(self, *_: object):
            raise httpx.ConnectError("offline")

    result = asyncio.run(ResilientCoach(UnavailableCoach(), RuleBasedCoach()).respond("Hello", []))

    assert result.reply.startswith("Hello, friend!")


def test_build_coach_uses_resilient_remote_provider_when_configured() -> None:
    configuration = Settings(llm_provider="github_models", openai_api_key="test-key")

    assert isinstance(build_coach(configuration), ResilientCoach)