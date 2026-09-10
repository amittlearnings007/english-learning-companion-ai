from __future__ import annotations

from io import BytesIO

import speech_recognition as speech_recognition
from gtts import gTTS

from app.config import settings
from app.services.languages import get_language
from app.services.utf8_guard import validate_utf8_text


class SpeechServiceError(RuntimeError):
    """Raised when an optional speech capability cannot fulfill a request."""


VOICE_TLDS = {
    "us": "com",
    "uk": "co.uk",
    "australia": "com.au",
}


class SpeechService:
    """Keeps speech binary in memory and validates all text at its boundaries."""

    def __init__(self, *, tts_enabled: bool = settings.tts_enabled, stt_enabled: bool = settings.stt_enabled) -> None:
        self.tts_enabled = tts_enabled
        self.stt_enabled = stt_enabled

    def synthesize(self, text: str, language: str = "en", voice: str = "us", speed: float = 1.0) -> bytes:
        validated_text = validate_utf8_text(text, "speech text")
        profile = get_language(language)
        if not self.tts_enabled:
            raise SpeechServiceError("Text-to-speech is disabled.")
        if voice not in VOICE_TLDS:
            raise SpeechServiceError("Unsupported voice selection.")
        try:
            audio_stream = BytesIO()
            gTTS(
                text=validated_text,
                lang=profile.code,
                tld=VOICE_TLDS[voice] if profile.code == "en" else "com",
                slow=speed < 0.9,
            ).write_to_fp(audio_stream)
            return audio_stream.getvalue()
        except Exception as error:
            raise SpeechServiceError("Text-to-speech is temporarily unavailable.") from error

    def transcribe(self, audio_content: bytes, language: str = "en") -> str:
        if not self.stt_enabled:
            raise SpeechServiceError("Speech-to-text is disabled.")
        if not audio_content:
            raise SpeechServiceError("Audio content is required.")
        try:
            recognizer = speech_recognition.Recognizer()
            profile = get_language(language)
            with speech_recognition.AudioFile(BytesIO(audio_content)) as source:
                audio_data = recognizer.record(source)
            transcript = recognizer.recognize_google(audio_data, language=profile.speech_code)
        except Exception as error:
            raise SpeechServiceError("Speech could not be transcribed. Please try again with a short WAV recording.") from error
        return validate_utf8_text(transcript, "speech transcript")