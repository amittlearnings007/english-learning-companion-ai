from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.utf8_guard import InvalidTextError, validate_utf8_text


TEXT_FILENAMES = {"Dockerfile", ".env", ".env.example"}
TEXT_SUFFIXES = {".css", ".html", ".js", ".json", ".md", ".py", ".sh", ".sql", ".toml", ".txt", ".yaml", ".yml"}


def staged_paths() -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [PROJECT_ROOT / path for path in result.stdout.splitlines()]


def should_validate(path: Path) -> bool:
    return path.name in TEXT_FILENAMES or path.suffix.lower() in TEXT_SUFFIXES


def validate_file(path: Path) -> str | None:
    if not path.exists() or not should_validate(path):
        return None
    try:
        text = path.read_text(encoding="utf-8")
        validate_utf8_text(text, f"file {path.relative_to(PROJECT_ROOT)}", allow_empty=True)
    except (InvalidTextError, UnicodeDecodeError) as error:
        return str(error)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate source files as UTF-8 text.")
    parser.add_argument("paths", nargs="*", type=Path, help="Files to validate; defaults to staged files.")
    arguments = parser.parse_args()
    paths = [path.resolve() for path in arguments.paths] if arguments.paths else staged_paths()
    failures = [(path, error) for path in paths if (error := validate_file(path))]
    if not failures:
        print("UTF-8 validation passed.")
        return 0
    for path, error in failures:
        print(f"UTF-8 validation failed: {path}: {error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())