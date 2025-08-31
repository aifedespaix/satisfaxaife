import os
from typing import Any

import pytest

from app.audio import WeaponAudio, get_default_engine, reset_default_engine
from app.core.config import settings
from app.core.types import Damage, EntityId
from app.game.match import create_controller
from app.render.renderer import Renderer
from app.video.recorder import Recorder
from app.weapons import weapon_registry
from app.weapons.base import Weapon, WorldView

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


class SpyWeaponAudio(WeaponAudio):
    """Weapon audio that records when the idle loop stops."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.stopped_at: float | None = None

    def stop_idle(self, timestamp: float | None = None) -> None:
        if self._idle_thread and self._idle_thread.is_alive() and self.stopped_at is None:
            self.stopped_at = timestamp
        super().stop_idle(timestamp)


class KillerWeapon(Weapon):
    """Weapon that instantly kills the opponent."""

    def __init__(self, audio: SpyWeaponAudio) -> None:
        super().__init__(name="killer", cooldown=0.0, damage=Damage(200))
        self.audio = audio
        self._done = False

    def update(self, owner: EntityId, view: WorldView, dt: float) -> None:
        if not self._done:
            enemy = view.get_enemy(owner)
            if enemy is not None:
                view.deal_damage(enemy, self.damage, timestamp=0.0)
                self._done = True
        super().update(owner, view, dt)


class PassiveWeapon(Weapon):
    """Weapon that never attacks."""

    def __init__(self, audio: SpyWeaponAudio) -> None:
        super().__init__(name="passive", cooldown=0.0, damage=Damage(0))
        self.audio = audio


class DummyRecorder(Recorder):
    """Recorder stub that captures the audio buffer."""

    def __init__(self) -> None:
        self.audio = None

    def add_frame(self, _frame: Any) -> None:
        return None

    def close(self, audio: Any = None, rate: int = 48_000) -> None:
        self.audio = audio


def test_winner_idle_sound_stops_on_victory() -> None:
    """Ensure the winner's idle sound stops when the match ends."""

    reset_default_engine()
    engine = get_default_engine()
    audio_a = SpyWeaponAudio("melee", "katana", engine=engine, idle_gap=0.01)
    audio_b = SpyWeaponAudio("melee", "katana", engine=engine, idle_gap=0.01)
    audio_a.start_idle(timestamp=0.0)
    audio_b.start_idle(timestamp=0.0)

    weapon_registry.register("killer_test", lambda: KillerWeapon(audio_a))
    weapon_registry.register("passive_test", lambda: PassiveWeapon(audio_b))

    recorder = DummyRecorder()
    renderer = Renderer(settings.width, settings.height)
    controller = create_controller("killer_test", "passive_test", recorder, renderer, max_seconds=1)
    controller.run()

    assert audio_a.stopped_at is not None
    assert controller.death_ts is not None
    assert audio_a.stopped_at == pytest.approx(controller.death_ts)
    intro_duration = controller.intro_manager._duration  # type: ignore[attr-defined]
    assert audio_a.stopped_at >= intro_duration
    assert audio_b.stopped_at is not None

    weapon_registry._factories.pop("killer_test")
    weapon_registry._factories.pop("passive_test")
    reset_default_engine()
