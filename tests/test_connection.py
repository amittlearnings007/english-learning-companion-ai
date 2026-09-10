from __future__ import annotations

import pytest

from app.database.connection import get_connection


def test_connection_rolls_back_database_errors(tmp_path) -> None:
    database_path = tmp_path / "rollback.db"
    with get_connection(database_path) as connection:
        connection.execute("CREATE TABLE notes (body TEXT NOT NULL)")

    with pytest.raises(RuntimeError):
        with get_connection(database_path) as connection:
            connection.execute("INSERT INTO notes (body) VALUES ('must not persist')")
            raise RuntimeError("force rollback")

    with get_connection(database_path) as connection:
        count = connection.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    assert count == 0