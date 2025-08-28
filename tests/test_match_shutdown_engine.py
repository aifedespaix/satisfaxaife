from __future__ import annotations

import numpy as np
import pytest

from app.audio import reset_default_engine
from app.audio.engine import AudioEngine
from app.core.config import settings
from app.game.match import MatchTimeout, run_match
from app.render.renderer import Renderer
from app.video.recorder import Recorder


class SpyRecorder(Recorder):
    """Recorder that captures the provided audio buffer."""

    def __init__(self) -> None:  # pragma: no cover - used in tests
        self.audio: np.ndarray | None = None

    def add_frame(self, _frame: np.ndarray) -> None:  # pragma: no cover - stub
        return None

    def close(self, audio: np.ndarray | None = None, rate: int = 48_000) -> None:  # pragma: no cover - stub
        self.audio = audio


def test_run_match_shuts_down_engine(monkeypatch: pytest.MonkeyPatch) -> None:
    shutdown_called = {"flag": False}

    def spy_shutdown(self: AudioEngine) -> None:  # pragma: no cover - spies
        shutdown_called["flag"] = True

    monkeypatch.setattr(AudioEngine, "shutdown", spy_shutdown)

    recorder = SpyRecorder()
    renderer = Renderer(settings.width, settings.height)
    with pytest.raises(MatchTimeout):
        run_match("katana", "katana", recorder, renderer, max_seconds=0)

    assert shutdown_called["flag"]
    reset_default_engine()
