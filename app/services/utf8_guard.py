from __future__ import annotations

import logging
from pathlib import Path


logger = logging.getLogger(__name__)
_ALLOWED_CONTROL_CHARACTERS = {"\n", "\r", "\t"}


class InvalidTextError(ValueError):
    """Raised when a persistence write is not safe UTF-8 text."""


def validate_utf8_text(value: object, field_name: str, *, allow_empty: bool = False) -> str:
    """Return valid text or reject non-text, binary-like, and invalid UTF-8 input."""
    if not isinstance(value, str):
        logger.warning("UTF-8 validation failed for %s: expected text", field_name)
        raise InvalidTextError(f"{field_name} must be UTF-8 text.")

    try:
        value.encode("utf-8", "strict")
    except UnicodeError as error:
        logger.warning("UTF-8 validation failed for %s: %s", field_name, error)
        raise InvalidTextError(f"{field_name} must be valid UTF-8 text.") from error

    if not allow_empty and not value.strip():
        logger.warning("UTF-8 validation failed for %s: blank text", field_name)
        raise InvalidTextError(f"{field_name} cannot be blank.")

    if any(ord(character) < 32 and character not in _ALLOWED_CONTROL_CHARACTERS for character in value):
        logger.warning("UTF-8 validation failed for %s: binary control character", field_name)
        raise InvalidTextError(f"{field_name} contains binary control characters.")

    return value


def write_utf8_text(path: Path, content: object) -> None:
    """Write validated UTF-8 text files through the same persistence guard."""
    validated_content = validate_utf8_text(content, "file content", allow_empty=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(validated_content, encoding="utf-8")