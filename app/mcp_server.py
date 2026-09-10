from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from app.database.repositories import LearningRepository


repository = LearningRepository()
repository.initialize()
mcp = FastMCP("English Learning Companion SQLite")


def _json_model(model: Any) -> dict[str, Any]:
    return model.model_dump(mode="json")


@mcp.tool()
def get_vocabulary(limit: int = 100) -> list[dict[str, Any]]:
    """Read the learner's vocabulary ordered by usage frequency."""
    return [_json_model(word) for word in repository.list_vocabulary(limit)]


@mcp.tool()
def add_word(word: str, meaning: str, example_sentence: str) -> dict[str, Any]:
    """Insert a word or increment frequency when it already exists."""
    return _json_model(repository.add_word(word, meaning, example_sentence))


@mcp.tool()
def update_frequency(word: str, increment: int = 1) -> dict[str, Any]:
    """Record another learner use of a stored vocabulary word."""
    return _json_model(repository.update_frequency(word, increment))


@mcp.tool()
def get_progress() -> dict[str, Any]:
    """Retrieve conversation, correction, and vocabulary progress statistics."""
    return _json_model(repository.get_progress())


@mcp.tool()
def save_conversation(user_message: str, ai_response: str, correction: str | None = None) -> dict[str, int]:
    """Save a completed coaching conversation and update learner progress."""
    return {"conversation_id": repository.save_conversation(user_message, ai_response, correction)}


if __name__ == "__main__":
    mcp.run(transport="stdio")