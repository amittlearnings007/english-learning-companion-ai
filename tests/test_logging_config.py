from __future__ import annotations

import logging

from app import logging_config


def test_logging_configuration_creates_utf8_log_file(monkeypatch, tmp_path) -> None:
    root_logger = logging.getLogger()
    existing_handlers = list(root_logger.handlers)
    original_configured = getattr(root_logger, "_lingo_configured", False)
    monkeypatch.setattr(logging_config, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(root_logger, "_lingo_configured", False, raising=False)
    try:
        logging_config.configure_logging()
        root_logger.warning("UTF-8 log: vocabulary")
        assert (tmp_path / "logs" / "application.log").read_text(encoding="utf-8")
    finally:
        for handler in list(root_logger.handlers):
            if handler not in existing_handlers:
                root_logger.removeHandler(handler)
                handler.close()
        root_logger._lingo_configured = original_configured  # type: ignore[attr-defined]