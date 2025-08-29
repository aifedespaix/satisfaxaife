from __future__ import annotations

from typing import TYPE_CHECKING

from app.audio import reset_default_engine
from app.audio.env import temporary_sdl_audio_driver
from app.core.config import settings
from app.game.match import run_match
from app.render.renderer import Renderer
from app.weapons import weapon_registry
from tests.integration.helpers import InstantKillWeapon, SpyRecorder

if TYPE_CHECKING:
    import numpy as np


class FrameSpyRecorder(SpyRecorder):
    """Recorder that counts frames and stores provided audio."""

    def __init__(self) -> None:
        super().__init__()
        self.frames = 0

    def add_frame(self, _frame: np.ndarray) -> None:  # pragma: no cover - stub
        self.frames += 1


def test_run_match_display_skips_capture() -> None:
    if "instakill" not in weapon_registry.names():
        weapon_registry.register("instakill", InstantKillWeapon)

    recorder = FrameSpyRecorder()
    with temporary_sdl_audio_driver("dummy"):
        renderer = Renderer(settings.width, settings.height)
        run_match("instakill", "instakill", recorder, renderer, max_seconds=1, display=True)
    assert recorder.frames == 0
    assert recorder.audio is None
    reset_default_engine()
