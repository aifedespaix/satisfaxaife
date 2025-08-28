from typing import cast

import numpy as np

from app.ai.policy import SimplePolicy
from app.audio import AudioEngine, reset_default_engine
from app.audio.balls import BallAudio
from app.audio.weapons import WeaponAudio
from app.core.config import settings
from app.core.types import Color, Damage, EntityId, Vec2
from app.game.match import Player, _MatchView, run_match
from app.render.renderer import Renderer
from app.video.recorder import Recorder
from app.weapons import weapon_registry
from app.weapons.base import Weapon, WorldView
from app.world.entities import Ball
from app.world.physics import PhysicsWorld


class StubWeaponAudio:
    """Minimal weapon audio stub tracking stop_idle calls."""

    def __init__(self) -> None:
        self.stop_idle_called = False

    def start_idle(self, timestamp: float | None = None) -> None:  # noqa: D401
        return None

    def stop_idle(self) -> None:  # noqa: D401
        self.stop_idle_called = True


class StubBallAudio:
    def on_explode(self, timestamp: float | None = None) -> None:  # noqa: D401
        return None


class StubRenderer:
    def add_impact(self, pos: Vec2, duration: float = 0.0) -> None:  # noqa: D401
        return None

    def trigger_blink(self, color: Color, amount: int) -> None:  # noqa: D401
        return None


class DummyWeapon(Weapon):
    def __init__(self) -> None:
        super().__init__(name="dummy", cooldown=0.0, damage=Damage(200))
        self.audio = cast(WeaponAudio, StubWeaponAudio())

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:  # noqa: D401
        return None


def test_player_death_stops_weapon_idle() -> None:
    world = PhysicsWorld()
    ball = Ball.spawn(world, (0.0, 0.0))
    weapon = DummyWeapon()
    player = Player(
        eid=ball.eid,
        ball=ball,
        weapon=weapon,
        policy=SimplePolicy("aggressive"),
        face=(1.0, 0.0),
        color=(255, 255, 255),
        audio=cast(BallAudio, StubBallAudio()),
    )
    renderer = cast(Renderer, StubRenderer())
    view = _MatchView([player], [], world, renderer, cast(AudioEngine, object()))
    view.deal_damage(player.eid, Damage(500), timestamp=0.0)
    stub = cast(StubWeaponAudio, weapon.audio)
    assert stub.stop_idle_called


class SpyRecorder(Recorder):
    def __init__(self) -> None:
        self.audio: np.ndarray | None = None

    def add_frame(self, _frame: np.ndarray) -> None:  # pragma: no cover - stub
        return None

    def close(
        self, audio: np.ndarray | None = None, rate: int = 48_000
    ) -> None:  # pragma: no cover - stub
        self.audio = audio


def test_run_match_stops_all_weapon_idle() -> None:
    audios: list[StubWeaponAudio] = []

    class IdleKillWeapon(Weapon):
        def __init__(self) -> None:
            super().__init__(name="idlekill", cooldown=0.0, damage=Damage(200))
            audio = StubWeaponAudio()
            self.audio = cast(WeaponAudio, audio)
            audios.append(audio)
            self._done = False

        def update(self, owner: EntityId, view: WorldView, dt: float) -> None:  # noqa: D401
            if not self._done:
                self.audio.start_idle()
                enemy = view.get_enemy(owner)
                if enemy is not None:
                    view.deal_damage(enemy, self.damage, timestamp=0.0)
                    self._done = True
            super().update(owner, view, dt)

        def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:  # noqa: D401
            return None

    if "idlekill" not in weapon_registry.names():
        weapon_registry.register("idlekill", IdleKillWeapon)

    recorder = SpyRecorder()
    renderer = Renderer(settings.width, settings.height)
    run_match("idlekill", "idlekill", recorder, renderer, max_seconds=1)

    assert len(audios) == 2
    assert all(a.stop_idle_called for a in audios)

    reset_default_engine()
