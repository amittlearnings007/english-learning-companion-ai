from __future__ import annotations

from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_streamlit_practice_view_renders_without_a_live_backend(monkeypatch) -> None:
    application = AppTest.from_file(Path(__file__).resolve().parents[1] / "app" / "ui" / "streamlit_app.py")

    application.run(timeout=15)

    assert not application.exception
    assert any("Talk & Play" in item.value for item in application.markdown)
    assert any("Talk to Lingo" in item.value for item in application.markdown)