from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from app.config import PROJECT_ROOT, settings


def configure_logging() -> None:
    """Configure concise console and UTF-8 rotating-file application logs once."""
    root_logger = logging.getLogger()
    if getattr(root_logger, "_lingo_configured", False):
        return

    log_path = PROJECT_ROOT / "logs" / "application.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
        errors="backslashreplace",
    )
    file_handler.setFormatter(formatter)
    root_logger.setLevel(settings.log_level.upper())
    root_logger.addHandler(file_handler)
    root_logger._lingo_configured = True  # type: ignore[attr-defined]