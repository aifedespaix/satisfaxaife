from __future__ import annotations

import os
from pathlib import Path

from app.audio import reset_default_engine
from app.core.config import settings
from app.game.match import create_controller
from app.render.renderer import Renderer


class DummyRecorder:
    """Recorder stub writing to a temporary path."""

    def __init__(self, path: Path) -> None:
        self.path: Path | None = path

    def add_frame(self, _frame: object) -> None:  # pragma: no cover - stub
        return None

    def close(self, audio: object | None = None, rate: int = 48_000) -> None:  # pragma: no cover - stub
        return None


def _match_duration(tmp_path: Path, parry: bool) -> float:
    reset_default_engine()
    recorder = DummyRecorder(tmp_path / "out.mp4")
    renderer = Renderer(settings.width, settings.height)
    controller = create_controller("knife", "knife", recorder, renderer, max_seconds=20)
    if not parry:
        for p in controller.players:
            p.policy.parry_window = 0.0
    controller.run()
    return controller.elapsed


def test_parry_slows_match(tmp_path: Path) -> None:
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    duration_no_parry = _match_duration(tmp_path, parry=False)
    duration_with_parry = _match_duration(tmp_path, parry=True)
    assert duration_with_parry > duration_no_parry
