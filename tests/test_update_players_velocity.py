from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pytest

from app.ai.stateful_policy import StatefulPolicy
from app.audio import AudioEngine, BallAudio
from app.core.config import settings
from app.core.types import EntityId
from app.game.controller import GameController, Player
from app.intro import IntroManager
from app.render.hud import Hud
from app.render.renderer import Renderer
from app.video.recorder import RecorderProtocol
from app.weapons.base import Weapon
from app.world.entities import Ball
from app.world.physics import PhysicsWorld
from pymunk import Body


class DummyWorld:
    def set_projectile_removed_callback(self, _cb: Any) -> None:
        return

    def set_context(self, _view: object, _timestamp: float) -> None:  # pragma: no cover - stub
        return

    def step(self, _dt: float, _substeps: int) -> None:  # pragma: no cover - stub
        return


class DummyWeapon:
    speed: float = 0.0

    def step(self, _dt: float) -> None:  # pragma: no cover - stub
        return

    def update(
        self, _owner: EntityId, _view: object, _dt: float
    ) -> None:  # pragma: no cover - stub
        return

    def trigger(
        self, _owner: EntityId, _view: object, _direction: tuple[float, float]
    ) -> None:  # pragma: no cover - stub
        return


class DummyPolicy:
    def __init__(self, accel: tuple[float, float]) -> None:
        self._accel = accel

    def decide(
        self, _eid: EntityId, _view: object, _now: float, _speed: float
    ) -> tuple[tuple[float, float], tuple[float, float], bool]:  # pragma: no cover - stub
        return self._accel, (1.0, 0.0), False

    def dash_direction(
        self, _eid: EntityId, _view: object, _now: float, _can_dash: bool
    ) -> None:  # pragma: no cover - stub
        return None


class DummyBallAudio:
    def on_hit(self, _timestamp: float | None = None) -> None:  # pragma: no cover - stub
        return

    def on_explode(self, _timestamp: float | None = None) -> None:  # pragma: no cover - stub
        return

    def stop_idle(self, _timestamp: float | None = None, *, disable: bool = False) -> None:  # pragma: no cover - stub
        return


class DummyBall:
    def __init__(self, vx: float, vy: float) -> None:
        self.body = Body(0.0, 0.0)
        self.body.velocity = (vx, vy)
        self.stats = SimpleNamespace(max_speed=100.0)
        self.health: float = 100.0

    def cap_speed(self) -> None:  # pragma: no cover - stub
        return


def _make_player(accel: tuple[float, float], initial_velocity: tuple[float, float]) -> Player:
    ball = cast(Ball, DummyBall(*initial_velocity))
    weapon = cast(Weapon, DummyWeapon())
    policy = cast(StatefulPolicy, DummyPolicy(accel))
    audio = cast(BallAudio, DummyBallAudio())
    return Player(EntityId(1), ball, weapon, policy, (1.0, 0.0), (0, 0, 0), audio)


def test_player_velocity_updates_from_acceleration() -> None:
    accel = (4.0, -5.0)
    initial_velocity = (1.0, -2.0)
    player = _make_player(accel, initial_velocity)

    world = cast(PhysicsWorld, DummyWorld())
    renderer = cast(Renderer, SimpleNamespace())
    hud = cast(Hud, SimpleNamespace())
    engine = cast(AudioEngine, SimpleNamespace())
    recorder = cast(
        RecorderProtocol,
        SimpleNamespace(add_frame=lambda _frame: None, close=lambda _audio=None, rate=48_000: None),
    )
    intro = cast(IntroManager, SimpleNamespace())

    controller = GameController(
        "a",
        "b",
        [player],
        world,
        renderer,
        hud,
        engine,
        recorder,
        intro,
    )

    controller._update_players(0.0)

    dt = settings.dt
    expected_vx = initial_velocity[0] + accel[0] * dt
    expected_vy = initial_velocity[1] + accel[1] * dt
    assert player.ball.body.velocity.x == pytest.approx(expected_vx)
    assert player.ball.body.velocity.y == pytest.approx(expected_vy)
