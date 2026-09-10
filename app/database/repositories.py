from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.database.connection import get_connection
from app.database.schema import initialize_database
from app.models.schemas import (
    ActivityPoint,
    ConversationItem,
    Correction,
    DashboardData,
    ProgressStats,
    VocabularyCandidate,
    VocabularyItem,
)
from app.services.utf8_guard import validate_utf8_text


class VocabularyNotFoundError(LookupError):
    """Raised when a frequency update targets an unknown vocabulary word."""


class LearningRepository:
    """Transactional SQLite persistence for learning activity."""

    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or settings.database_path

    def initialize(self) -> None:
        with get_connection(self.database_path) as connection:
            initialize_database(connection)

    def list_vocabulary(self, limit: int = 100) -> list[VocabularyItem]:
        with get_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, word, meaning, example_sentence, learned_date, frequency
                FROM vocabulary
                ORDER BY frequency DESC, learned_date DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._vocabulary_from_row(row) for row in rows]

    def add_word(
        self,
        word: str,
        meaning: str,
        example_sentence: str,
        *,
        frequency: int = 1,
    ) -> VocabularyItem:
        candidate = self._validate_candidate(
            VocabularyCandidate(word=word, meaning=meaning, example_sentence=example_sentence)
        )
        with get_connection(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO vocabulary (word, meaning, example_sentence, frequency)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(word) DO UPDATE SET
                    frequency = vocabulary.frequency + excluded.frequency,
                    example_sentence = excluded.example_sentence
                """,
                (candidate.word, candidate.meaning, candidate.example_sentence, frequency),
            )
            row = connection.execute(
                """
                SELECT id, word, meaning, example_sentence, learned_date, frequency
                FROM vocabulary WHERE word = ? COLLATE NOCASE
                """,
                (candidate.word,),
            ).fetchone()
            self._sync_vocabulary_count(connection)
        return self._vocabulary_from_row(row)

    def update_frequency(self, word: str, increment: int = 1) -> VocabularyItem:
        validated_word = validate_utf8_text(word, "word")
        with get_connection(self.database_path) as connection:
            cursor = connection.execute(
                "UPDATE vocabulary SET frequency = frequency + ? WHERE word = ? COLLATE NOCASE",
                (increment, validated_word),
            )
            if cursor.rowcount == 0:
                raise VocabularyNotFoundError(f"Vocabulary word not found: {validated_word}")
            row = connection.execute(
                """
                SELECT id, word, meaning, example_sentence, learned_date, frequency
                FROM vocabulary WHERE word = ? COLLATE NOCASE
                """,
                (validated_word,),
            ).fetchone()
        return self._vocabulary_from_row(row)

    def save_turn(
        self,
        user_message: str,
        ai_response: str,
        correction: Correction | None,
        vocabulary: Iterable[VocabularyCandidate],
    ) -> tuple[int, list[VocabularyItem]]:
        validated_user_message = validate_utf8_text(user_message, "user message")
        validated_ai_response = validate_utf8_text(ai_response, "AI response")
        correction_text = self._correction_text(correction)
        candidates = self._unique_candidates(vocabulary)

        with get_connection(self.database_path) as connection:
            cursor = connection.execute(
                "INSERT INTO conversations (user_message, ai_response, correction) VALUES (?, ?, ?)",
                (validated_user_message, validated_ai_response, correction_text),
            )
            for candidate in candidates:
                connection.execute(
                    """
                    INSERT INTO vocabulary (word, meaning, example_sentence, frequency)
                    VALUES (?, ?, ?, 1)
                    ON CONFLICT(word) DO UPDATE SET frequency = vocabulary.frequency + 1
                    """,
                    (candidate.word, candidate.meaning, candidate.example_sentence),
                )
            vocabulary_count = self._sync_vocabulary_count(connection)
            connection.execute(
                """
                UPDATE progress
                SET total_messages = total_messages + 1,
                    corrections_given = corrections_given + ?,
                    vocabulary_count = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = 1
                """,
                (1 if correction else 0, vocabulary_count),
            )
            saved_vocabulary = [self._find_word(connection, candidate.word) for candidate in candidates]
        return int(cursor.lastrowid), saved_vocabulary

    def save_conversation(self, user_message: str, ai_response: str, correction: str | None = None) -> int:
        validated_user_message = validate_utf8_text(user_message, "user message")
        validated_ai_response = validate_utf8_text(ai_response, "AI response")
        validated_correction = validate_utf8_text(correction, "correction") if correction else None
        with get_connection(self.database_path) as connection:
            cursor = connection.execute(
                "INSERT INTO conversations (user_message, ai_response, correction) VALUES (?, ?, ?)",
                (validated_user_message, validated_ai_response, validated_correction),
            )
            vocabulary_count = self._sync_vocabulary_count(connection)
            connection.execute(
                """
                UPDATE progress
                SET total_messages = total_messages + 1,
                    corrections_given = corrections_given + ?,
                    vocabulary_count = ?,
                    last_updated = CURRENT_TIMESTAMP
                WHERE id = 1
                """,
                (1 if validated_correction else 0, vocabulary_count),
            )
        return int(cursor.lastrowid)

    def get_conversations(self, limit: int = 20) -> list[ConversationItem]:
        with get_connection(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, user_message, ai_response, correction, timestamp
                FROM conversations ORDER BY timestamp DESC, id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            ConversationItem(
                id=row["id"],
                user_message=row["user_message"],
                ai_response=row["ai_response"],
                correction=row["correction"],
                timestamp=self._to_datetime(row["timestamp"]),
            )
            for row in rows
        ]

    def get_progress(self) -> ProgressStats:
        with get_connection(self.database_path) as connection:
            self._sync_vocabulary_count(connection)
            row = connection.execute(
                """
                SELECT total_messages, corrections_given, vocabulary_count, last_updated
                FROM progress WHERE id = 1
                """
            ).fetchone()
        return ProgressStats(
            total_messages=row["total_messages"],
            corrections_given=row["corrections_given"],
            vocabulary_count=row["vocabulary_count"],
            last_updated=self._to_datetime(row["last_updated"]),
        )

    def get_dashboard(self) -> DashboardData:
        with get_connection(self.database_path) as connection:
            self._sync_vocabulary_count(connection)
            progress = connection.execute(
                """
                SELECT total_messages, corrections_given, vocabulary_count, last_updated
                FROM progress WHERE id = 1
                """
            ).fetchone()
            most_used_rows = connection.execute(
                """
                SELECT id, word, meaning, example_sentence, learned_date, frequency
                FROM vocabulary ORDER BY frequency DESC, word ASC LIMIT 5
                """
            ).fetchall()
            activity_rows = connection.execute(
                """
                SELECT DATE(timestamp) AS date, COUNT(*) AS count
                FROM conversations GROUP BY DATE(timestamp) ORDER BY date
                """
            ).fetchall()
            weekly_rows = connection.execute(
                """
                SELECT strftime('%Y-W%W', learned_date) AS date, COUNT(*) AS count
                FROM vocabulary GROUP BY strftime('%Y-W%W', learned_date) ORDER BY date
                """
            ).fetchall()
            correction_rows = connection.execute(
                """
                SELECT DATE(timestamp) AS date, COUNT(*) AS count
                FROM conversations WHERE correction IS NOT NULL
                GROUP BY DATE(timestamp) ORDER BY date
                """
            ).fetchall()
        return DashboardData(
            progress=ProgressStats(
                total_messages=progress["total_messages"],
                corrections_given=progress["corrections_given"],
                vocabulary_count=progress["vocabulary_count"],
                last_updated=self._to_datetime(progress["last_updated"]),
            ),
            most_used_words=[self._vocabulary_from_row(row) for row in most_used_rows],
            daily_activity=self._activity_points(activity_rows),
            new_words_per_week=self._activity_points(weekly_rows),
            corrections_by_date=self._activity_points(correction_rows),
        )

    def _validate_candidate(self, candidate: VocabularyCandidate) -> VocabularyCandidate:
        return VocabularyCandidate(
            word=validate_utf8_text(candidate.word.strip().lower(), "word"),
            meaning=validate_utf8_text(candidate.meaning, "meaning"),
            example_sentence=validate_utf8_text(candidate.example_sentence, "example sentence"),
        )

    def _unique_candidates(self, candidates: Iterable[VocabularyCandidate]) -> list[VocabularyCandidate]:
        unique_candidates: list[VocabularyCandidate] = []
        seen_words: set[str] = set()
        for candidate in candidates:
            validated = self._validate_candidate(candidate)
            if validated.word not in seen_words:
                unique_candidates.append(validated)
                seen_words.add(validated.word)
        return unique_candidates

    def _correction_text(self, correction: Correction | None) -> str | None:
        if correction is None:
            return None
        original = validate_utf8_text(correction.original, "correction original")
        corrected = validate_utf8_text(correction.corrected, "correction corrected")
        reason = validate_utf8_text(correction.reason, "correction reason")
        return f"{original} -> {corrected}. {reason}"

    @staticmethod
    def _sync_vocabulary_count(connection: sqlite3.Connection) -> int:
        count = int(connection.execute("SELECT COUNT(*) FROM vocabulary").fetchone()[0])
        connection.execute(
            "UPDATE progress SET vocabulary_count = ?, last_updated = CURRENT_TIMESTAMP WHERE id = 1",
            (count,),
        )
        return count

    def _find_word(self, connection: sqlite3.Connection, word: str) -> VocabularyItem:
        row = connection.execute(
            """
            SELECT id, word, meaning, example_sentence, learned_date, frequency
            FROM vocabulary WHERE word = ? COLLATE NOCASE
            """,
            (word,),
        ).fetchone()
        return self._vocabulary_from_row(row)

    @staticmethod
    def _vocabulary_from_row(row: sqlite3.Row) -> VocabularyItem:
        return VocabularyItem(
            id=row["id"],
            word=row["word"],
            meaning=row["meaning"],
            example_sentence=row["example_sentence"],
            learned_date=LearningRepository._to_datetime(row["learned_date"]),
            frequency=row["frequency"],
        )

    @staticmethod
    def _activity_points(rows: Iterable[sqlite3.Row]) -> list[ActivityPoint]:
        return [ActivityPoint(date=row["date"], count=row["count"]) for row in rows]

    @staticmethod
    def _to_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value)