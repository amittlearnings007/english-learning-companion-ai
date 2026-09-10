from __future__ import annotations

import pytest

from app.services.utf8_guard import InvalidTextError
from app.speech.service import SpeechService, SpeechServiceError


def test_speech_service_rejects_invalid_text_before_synthesis() -> None:
    service = SpeechService()

    with pytest.raises(InvalidTextError):
        service.synthesize("bad\x00text")


def test_speech_service_reports_disabled_text_to_speech() -> None:
    service = SpeechService(tts_enabled=False)

    with pytest.raises(SpeechServiceError, match="disabled"):
        service.synthesize("Hello")


def test_speech_service_reports_disabled_speech_to_text() -> None:
    service = SpeechService(stt_enabled=False)

    with pytest.raises(SpeechServiceError, match="disabled"):
        service.transcribe(b"audio")


def test_speech_service_synthesizes_audio_with_selected_voice(monkeypatch) -> None:
    class FakeTts:
        arguments: dict[str, object] | None = None

        def __init__(self, **kwargs: object) -> None:
            FakeTts.arguments = kwargs

        def write_to_fp(self, stream) -> None:
            stream.write(b"fake-mp3")

    monkeypatch.setattr("app.speech.service.gTTS", FakeTts)

    audio = SpeechService().synthesize("Hello, learner.", voice="uk", speed=0.8)

    assert audio == b"fake-mp3"
    assert FakeTts.arguments == {"text": "Hello, learner.", "lang": "en", "tld": "co.uk", "slow": True}


def test_speech_service_transcribes_audio(monkeypatch) -> None:
    class FakeAudioFile:
        def __init__(self, stream) -> None:
            self.stream = stream

        def __enter__(self) -> str:
            return "audio-source"

        def __exit__(self, *_: object) -> None:
            return None

    class FakeRecognizer:
        def record(self, source: str) -> str:
            assert source == "audio-source"
            return "audio-data"

        def recognize_google(self, audio_data: str, language: str) -> str:
            assert audio_data == "audio-data"
            assert language == "en-US"
            return "I feel confident today."

    monkeypatch.setattr("app.speech.service.speech_recognition.AudioFile", FakeAudioFile)
    monkeypatch.setattr("app.speech.service.speech_recognition.Recognizer", FakeRecognizer)

    assert SpeechService().transcribe(b"wav data") == "I feel confident today."


def test_speech_service_reports_provider_failure(monkeypatch) -> None:
    class FailingTts:
        def __init__(self, **_: object) -> None:
            raise OSError("network unavailable")

    monkeypatch.setattr("app.speech.service.gTTS", FailingTts)

    with pytest.raises(SpeechServiceError, match="temporarily unavailable"):
        SpeechService().synthesize("Hello")


def test_speech_service_uses_selected_language(monkeypatch) -> None:
    class FakeTts:
        arguments: dict[str, object] | None = None

        def __init__(self, **kwargs: object) -> None:
            FakeTts.arguments = kwargs

        def write_to_fp(self, stream) -> None:
            stream.write(b"hola-mp3")

    monkeypatch.setattr("app.speech.service.gTTS", FakeTts)

    assert SpeechService().synthesize("Hola, amigo.", language="es") == b"hola-mp3"
    assert FakeTts.arguments == {"text": "Hola, amigo.", "lang": "es", "tld": "com", "slow": False}