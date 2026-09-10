from __future__ import annotations

import logging

import pytest

from app.services.utf8_guard import InvalidTextError, validate_utf8_text, write_utf8_text


def test_validate_utf8_text_accepts_unicode_text() -> None:
    assert validate_utf8_text("I am fascinated by astronomy.", "message") == "I am fascinated by astronomy."


@pytest.mark.parametrize("value", [b"binary", 42, None, "\x00not text"])
def test_validate_utf8_text_rejects_non_text_or_binary_content(value: object) -> None:
    with pytest.raises(InvalidTextError):
        validate_utf8_text(value, "message")


def test_write_utf8_text_creates_valid_utf8_file(tmp_path) -> None:
    target = tmp_path / "note.txt"
    write_utf8_text(target, "Vocabulary: fascinated")
    assert target.read_text(encoding="utf-8") == "Vocabulary: fascinated"


def test_validation_failure_is_logged(caplog) -> None:
    with caplog.at_level(logging.WARNING):
        with pytest.raises(InvalidTextError):
            validate_utf8_text(b"not text", "message")

    assert "UTF-8 validation failed for message" in caplog.text