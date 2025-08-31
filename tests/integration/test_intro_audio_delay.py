from __future__ import annotations

from pathlib import Path
from typing import Any

from app.audio import AudioEngine, reset_default_engine
from app.audio.env import temporary_sdl_audio_driver
from app.core.config import settings
from app.core.types import Damage, EntityId, Vec2
from app.game.match import create_controller
from app.intro import IntroConfig, IntroManager
from app.render.renderer import Renderer
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


class SpyRecorder:
    """Recorder that retains the provided audio buffer."""

    def __init__(self) -> None:
        self.path: Path | None = None
        self.audio: Any | None = None

    def add_frame(self, _frame: Any) -> None:  # pragma: no cover - stub
        return

    def close(self, audio: Any | None = None, rate: int = 48_000) -> None:  # noqa: D401 - same interface
        self.audio = audio


def test_audio_starts_after_intro() -> None:
    intro_duration = 0.05
    if "instakill" not in weapon_registry.names():
        weapon_registry.register("instakill", InstantKillWeapon)

    with temporary_sdl_audio_driver("dummy"):
        recorder = SpyRecorder()
        renderer = Renderer(settings.width, settings.height)
        controller = create_controller("instakill", "instakill", recorder, renderer, max_seconds=1)
        controller.intro_manager = IntroManager(
            config=IntroConfig(
                logo_in=intro_duration,
                weapons_in=0.0,
                hold=0.0,
                fade_out=0.0,
                allow_skip=False,
            )
        )
        controller.intro_manager.start()
        engine = controller.engine
        engine.start_capture()

        while not controller.intro_manager.is_finished():
            controller.intro_manager.update(settings.dt)

        player = controller.players[0]
        player.weapon.update(player.eid, controller.view, settings.dt)

        audio = engine.end_capture()
        engine.shutdown()

    intro_samples = int(intro_duration * AudioEngine.SAMPLE_RATE)
    first = next((i for i, sample in enumerate(audio) if sample.any()), None)
    assert first is not None and first >= intro_samples
    reset_default_engine()
