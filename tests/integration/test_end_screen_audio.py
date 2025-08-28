from __future__ import annotations

import numpy as np
import pytest

from app.audio import AudioEngine, reset_default_engine
from app.audio.env import temporary_sdl_audio_driver
from app.core.config import settings
from app.core.types import Damage, EntityId, Vec2
from app.game.match import _append_slowmo_segment, run_match
from app.render.renderer import Renderer
from app.video.recorder import Recorder
from app.weapons import weapon_registry
from app.weapons.base import Weapon, WorldView

EVENT_TIME = 0.1


class InstantKillWeapon(Weapon):
    """Weapon that immediately destroys the opponent."""

    def __init__(self) -> None:
        super().__init__(name="instakill", cooldown=0.0, damage=Damage(200))
        self._done = False

    def _fire(
        self, owner: EntityId, view: WorldView, direction: Vec2
    ) -> None:  # pragma: no cover - stub
        return None

    def update(self, owner: EntityId, view: WorldView, dt: float) -> None:
        if not self._done:
            enemy = view.get_enemy(owner)
            if enemy is not None:
                view.deal_damage(enemy, self.damage, timestamp=EVENT_TIME)
                self._done = True
        super().update(owner, view, dt)


class SpyRecorder(Recorder):
    """Recorder that retains the provided audio buffer."""

    def __init__(self) -> None:
        self.audio: np.ndarray | None = None

    def add_frame(self, _frame: np.ndarray) -> None:  # pragma: no cover - stub
        return

    def close(
        self, audio: np.ndarray | None = None, rate: int = 48_000
    ) -> None:  # pragma: no cover - stub
        self.audio = audio


@pytest.mark.integration
@pytest.mark.usefixtures("monkeypatch")
def test_end_screen_audio_contains_explosion_and_slow_segment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Audio replay should be longer and contain the kill sound."""

    if "instakill" not in weapon_registry.names():
        weapon_registry.register("instakill", InstantKillWeapon)

    recorder = SpyRecorder()
    renderer = Renderer(settings.width, settings.height)

    captured: dict[str, np.ndarray] = {}
    original = _append_slowmo_segment

    def capture(audio: np.ndarray, engine: AudioEngine) -> np.ndarray:
        captured["real"] = audio.copy()
        return original(audio, engine)

    monkeypatch.setattr("app.game.match._append_slowmo_segment", capture)

    with temporary_sdl_audio_driver("dummy"):
        run_match("instakill", "instakill", recorder, renderer, max_seconds=1)

    raw = captured["real"]
    final = recorder.audio
    assert final is not None

    slow_samples = int(settings.end_screen.slowmo_duration * AudioEngine.SAMPLE_RATE)
    pad_samples = int(settings.end_screen.pre_slowmo_ms / 1000 * AudioEngine.SAMPLE_RATE)
    segment_len = min(raw.shape[0], slow_samples)
    expected = raw.shape[0] + pad_samples + int(segment_len / settings.end_screen.slowmo)
    tolerance = AudioEngine.SAMPLE_RATE // settings.fps

    assert final.shape[0] > raw.shape[0]
    assert abs(final.shape[0] - expected) <= tolerance

    kill_sample = int(EVENT_TIME * AudioEngine.SAMPLE_RATE)
    segment_start = max(0, raw.shape[0] - slow_samples)
    offset = kill_sample - segment_start
    slow_start = raw.shape[0] + pad_samples
    explosion_index = slow_start + int(offset / settings.end_screen.slowmo)
    window = final[explosion_index : explosion_index + 200]
    assert np.any(window != 0)

    reset_default_engine()
