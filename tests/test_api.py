from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import create_app
from app.speech.service import SpeechService


@pytest.fixture
def client(tmp_path):
    application = create_app(database_path=tmp_path / "api.db")
    with TestClient(application) as test_client:
        yield test_client


def test_chat_saves_turn_and_returns_one_correction(client) -> None:
    response = client.post("/api/chat", json={"message": "Yesterday I go to market and buy some fruits."})

    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Yummy! Which fruit do you like?"
    assert body["correction"]["corrected"] == "Yesterday I went to the market and bought some fruits."
    assert client.get("/api/progress").json()["total_messages"] == 1


def test_vocabulary_api_tracks_frequency(client) -> None:
    payload = {
        "word": "fascinated",
        "meaning": "extremely interested",
        "example_sentence": "I am fascinated by astronomy.",
    }
    assert client.post("/api/vocabulary", json=payload).status_code == 201
    response = client.patch("/api/vocabulary/fascinated/frequency", json={"increment": 2})

    assert response.status_code == 200
    assert response.json()["frequency"] == 3


def test_api_rejects_binary_like_text_before_database_write(client) -> None:
    payload = {
        "word": "bad\u0000word",
        "meaning": "invalid",
        "example_sentence": "This must not persist.",
    }
    response = client.post("/api/vocabulary", json=payload)

    assert response.status_code == 400
    assert client.get("/api/vocabulary").json() == []


def test_utf8_middleware_rejects_malformed_json_before_request_parsing(client) -> None:
    response = client.post(
        "/api/chat",
        content=b'{"message":"\xff"}',
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Request body must contain valid UTF-8 text."
    assert client.get("/api/progress").json()["total_messages"] == 0


def test_dashboard_exposes_chart_data(client) -> None:
    client.post("/api/chat", json={"message": "I am fascinated by astronomy."})
    dashboard = client.get("/api/dashboard")

    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["progress"]["vocabulary_count"] == 2
    assert len(body["daily_activity"]) == 1


def test_practice_suggestions_use_saved_vocabulary(client) -> None:
    client.post(
        "/api/vocabulary",
        json={
            "word": "confident",
            "meaning": "sure of yourself",
            "example_sentence": "I feel confident today.",
        },
    )

    response = client.get("/api/practice-suggestions")

    assert response.status_code == 200
    assert response.json()[0]["word"] == "confident"
    assert response.json()[0]["focus"] == "Say and show it"
    assert "Write" not in response.json()[0]["prompt"]


def test_conversation_history_and_missing_word_errors(client) -> None:
    client.post("/api/chat", json={"message": "Hello"})

    conversations = client.get("/api/conversations?limit=5")
    missing_word = client.patch("/api/vocabulary/unknown/frequency", json={"increment": 1})

    assert conversations.status_code == 200
    assert conversations.json()[0]["user_message"] == "Hello"
    assert missing_word.status_code == 404


def test_speech_routes_report_disabled_services(tmp_path) -> None:
    application = create_app(database_path=tmp_path / "speech-api.db")
    with TestClient(application) as client:
        application.state.speech_service = SpeechService(tts_enabled=False, stt_enabled=False)

        status_response = client.get("/api/speech/status")
        synthesize_response = client.post("/api/speech/synthesize", params={"text": "Hello"})
        transcribe_response = client.post(
            "/api/speech/transcribe",
            files={"audio": ("message.wav", b"not a real wav", "audio/wav")},
        )

    assert status_response.json() == {"text_to_speech": False, "speech_to_text": False}
    assert synthesize_response.status_code == 503
    assert transcribe_response.status_code == 503


def test_health_endpoint_is_available(client) -> None:
    assert client.get("/health").json()["status"] == "ok"


def test_languages_endpoint_exposes_provider_supported_speech_codes(client) -> None:
    response = client.get("/api/languages")

    assert response.status_code == 200
    languages = response.json()
    assert len(languages) >= 60
    assert {language["code"] for language in languages}.issuperset({"en", "es", "hi", "zh-CN"})
    assert languages[0]["code"] == "en"


def test_chat_can_use_a_selected_learning_language(client) -> None:
    response = client.post("/api/chat", json={"message": "Hello", "language": "es"})

    assert response.status_code == 200
    assert response.json()["language"] == "es"
    assert response.json()["reply"].startswith("¡Hola")