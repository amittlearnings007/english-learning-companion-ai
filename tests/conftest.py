from __future__ import annotations

import pytest

from app.database.repositories import LearningRepository


@pytest.fixture
def repository(tmp_path):
    learning_repository = LearningRepository(tmp_path / "learning.db")
    learning_repository.initialize()
    return learning_repository