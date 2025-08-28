from __future__ import annotations

import numpy as np

from app.audio import AudioEngine, reset_default_engine
from app.core.config import settings
from app.core.types import Damage, EntityId, Vec2
from app.game.match import run_match
from app.render.renderer import Renderer
from app.video.recorder import Recorder
from app.weapons import weapon_registry
from app.weapons.base import Weapon, WorldView

EVENT_TIME = 0.1


class InstantKillWeapon(Weapon):
    """Weapon that instantly kills the opposing player."""

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


def test_headless_match_records_kill_audio() -> None:
    if "instakill" not in weapon_registry.names():
        weapon_registry.register("instakill", InstantKillWeapon)

    recorder = SpyRecorder()
    renderer = Renderer(settings.width, settings.height)
    run_match("instakill", "instakill", recorder, renderer, max_seconds=1)
    assert recorder.audio is not None

    kill_sample = int(EVENT_TIME * AudioEngine.SAMPLE_RATE)
    window = recorder.audio[kill_sample : kill_sample + 200]
    assert np.any(window != 0)

    reset_default_engine()
