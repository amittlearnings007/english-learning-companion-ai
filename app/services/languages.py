from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from gtts.lang import tts_langs


@dataclass(frozen=True, slots=True)
class LanguageProfile:
    code: str
    name: str
    native_name: str
    speech_code: str


# Native labels make the selector friendly while gTTS supplies the supported-code catalog.
NATIVE_NAMES = {
    "af": "Afrikaans",
    "am": "አማርኛ",
    "ar": "العربية",
    "bn": "বাংলা",
    "bg": "Български",
    "ca": "Català",
    "cs": "Čeština",
    "da": "Dansk",
    "de": "Deutsch",
    "el": "Ελληνικά",
    "en": "English",
    "es": "Español",
    "fi": "Suomi",
    "fr": "Français",
    "gu": "ગુજરાતી",
    "he": "עברית",
    "hi": "हिन्दी",
    "iw": "עברית",
    "id": "Bahasa Indonesia",
    "it": "Italiano",
    "ja": "日本語",
    "kn": "ಕನ್ನಡ",
    "ko": "한국어",
    "ml": "മലയാളം",
    "mr": "मराठी",
    "ms": "Bahasa Melayu",
    "nl": "Nederlands",
    "no": "Norsk",
    "pa": "ਪੰਜਾਬੀ",
    "pl": "Polski",
    "pt": "Português (Brasil)",
    "pt-PT": "Português (Portugal)",
    "ro": "Română",
    "ru": "Русский",
    "si": "සිංහල",
    "sk": "Slovenčina",
    "sq": "Shqip",
    "sv": "Svenska",
    "sw": "Kiswahili",
    "ta": "தமிழ்",
    "te": "తెలుగు",
    "th": "ไทย",
    "tl": "Filipino",
    "tr": "Türkçe",
    "uk": "Українська",
    "ur": "اردو",
    "vi": "Tiếng Việt",
    "yue": "粵語",
    "zh": "中文",
    "zh-CN": "简体中文",
    "zh-TW": "繁體中文",
}

SPEECH_CODES = {
    "en": "en-US",
    "fr": "fr-FR",
    "de": "de-DE",
    "es": "es-ES",
    "pt": "pt-BR",
    "pt-PT": "pt-PT",
    "zh": "zh-CN",
    "zh-CN": "zh-CN",
    "zh-TW": "zh-TW",
    "yue": "yue-Hant-HK",
    "iw": "he-IL",
}


@lru_cache(maxsize=1)
def language_catalog() -> tuple[LanguageProfile, ...]:
    """Return the installed gTTS/Google-supported language catalog.

    The provider ships this catalog from Google Translate's language list. A small
    fallback keeps the app bootable if a future provider release changes its API.
    """
    try:
        supported = tts_langs()
    except Exception:
        supported = {"en": "English", "es": "Spanish", "fr": "French", "hi": "Hindi"}

    ordered_codes = ["en"] + sorted(code for code in supported if code != "en")
    return tuple(
        LanguageProfile(
            code=code,
            name=supported[code],
            native_name=NATIVE_NAMES.get(code, supported[code]),
            speech_code=SPEECH_CODES.get(code, code),
        )
        for code in ordered_codes
        if code in supported
    )


def get_language(code: str) -> LanguageProfile:
    """Resolve a gTTS code or its speech-recognition alias."""
    for profile in language_catalog():
        if profile.code == code or profile.speech_code.lower() == code.lower():
            return profile
    raise ValueError(f"Unsupported learning language: {code}")