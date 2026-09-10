from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = (Path(__file__).with_name("schema.sql")).read_text(encoding="utf-8")


def initialize_database(connection: sqlite3.Connection) -> None:
    """Create the application schema and the singleton progress record."""
    connection.executescript(SCHEMA)
    connection.execute(
        """
        INSERT INTO progress (id, total_messages, corrections_given, vocabulary_count)
        VALUES (1, 0, 0, 0)
        ON CONFLICT(id) DO NOTHING
        """
    )