from __future__ import annotations

import numpy as np

from app.core.types import Damage, EntityId, Vec2
from app.video.recorder import Recorder
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
