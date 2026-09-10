from __future__ import annotations

import pytest

from app.models.schemas import Correction, VocabularyCandidate
from app.services.utf8_guard import InvalidTextError


def test_add_word_increments_frequency_for_repeated_words(repository) -> None:
    first = repository.add_word("fascinated", "extremely interested", "I am fascinated by astronomy.")
    second = repository.add_word("fascinated", "extremely interested", "She is fascinated by space.")

    assert first.frequency == 1
    assert second.frequency == 2
    assert second.example_sentence == "She is fascinated by space."


def test_save_turn_tracks_conversation_vocabulary_and_progress(repository) -> None:
    correction = Correction(
        original="I am agree",
        corrected="I agree",
        reason="Use agree as a verb.",
    )
    conversation_id, vocabulary = repository.save_turn(
        "I am fascinated by astronomy.",
        "That is a fascinating subject.",
        correction,
        [VocabularyCandidate(word="fascinated", meaning="extremely interested", example_sentence="I am fascinated by astronomy.")],
    )

    progress = repository.get_progress()
    assert conversation_id == 1
    assert vocabulary[0].word == "fascinated"
    assert progress.total_messages == 1
    assert progress.corrections_given == 1
    assert progress.vocabulary_count == 1


def test_invalid_text_never_creates_a_vocabulary_record(repository) -> None:
    with pytest.raises(InvalidTextError):
        repository.add_word("bad\x00word", "invalid", "This write must fail.")

    assert repository.list_vocabulary() == []


def test_dashboard_reports_learning_data(repository) -> None:
    repository.save_conversation("Hello", "Hello!", None)
    repository.add_word("confident", "sure of yourself", "I feel confident today.")

    dashboard = repository.get_dashboard()
    assert dashboard.progress.total_messages == 1
    assert dashboard.progress.vocabulary_count == 1
    assert dashboard.most_used_words[0].word == "confident"
    assert dashboard.daily_activity[0].count == 1