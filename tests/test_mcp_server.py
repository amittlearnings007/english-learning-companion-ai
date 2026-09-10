from __future__ import annotations

from app import mcp_server
from app.database.repositories import LearningRepository


def test_sqlite_mcp_tools_read_write_and_track_learning(monkeypatch, tmp_path) -> None:
    repository = LearningRepository(tmp_path / "mcp.db")
    repository.initialize()
    monkeypatch.setattr(mcp_server, "repository", repository)

    word = mcp_server.add_word("curious", "wanting to know more", "I am curious about space.")
    updated = mcp_server.update_frequency("curious", increment=2)
    conversation = mcp_server.save_conversation("Hello", "Hello!", "No correction needed.")
    vocabulary = mcp_server.get_vocabulary()
    progress = mcp_server.get_progress()

    assert word["word"] == "curious"
    assert updated["frequency"] == 3
    assert conversation["conversation_id"] == 1
    assert vocabulary[0]["word"] == "curious"
    assert progress == {"total_messages": 1, "corrections_given": 1, "vocabulary_count": 1, "last_updated": progress["last_updated"]}