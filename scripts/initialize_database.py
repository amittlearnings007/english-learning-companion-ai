from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.repositories import LearningRepository


if __name__ == "__main__":
    repository = LearningRepository()
    repository.initialize()
    print(f"Initialized SQLite database at {repository.database_path}")