from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from app.ai.stateful_policy import StatefulPolicy
from app.audio import AudioEngine, BallAudio
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

    def parry(self, _owner: EntityId, _view: object) -> None:  # pragma: no cover - stub
        return

    def trigger(
        self, _owner: EntityId, _view: object, _direction: tuple[float, float]
    ) -> None:  # pragma: no cover - stub
        return


class DummyPolicy:
    def decide(
        self, _eid: EntityId, _view: object, _speed: float
    ) -> tuple[tuple[float, float], tuple[float, float], bool, bool]:
        return (0.0, 0.0), (1.0, 0.0), False, False

    def dash_direction(
        self, _eid: EntityId, _view: object, _now: float, _can_dash: Any
    ) -> tuple[float, float]:
        return (1.0, 0.0)


class DummyBallAudio:
    def on_hit(self, _timestamp: float | None = None) -> None:  # pragma: no cover - stub
        return

    def on_explode(self, _timestamp: float | None = None) -> None:  # pragma: no cover - stub
        return

    def stop_idle(self, _timestamp: float | None = None) -> None:  # pragma: no cover - stub
        return


class DummyBall:
    def __init__(self) -> None:
        self.body = Body(0.0, 0.0)
        self.body.velocity = (0.0, 0.0)
        self.stats = SimpleNamespace(max_speed=100.0)
        self.health: float = 100.0

    def cap_speed(self) -> None:  # pragma: no cover - stub
        return


class DummyEngine:
    def __init__(self) -> None:
        self.paths: list[str] = []
        self.timestamps: list[float | None] = []

    def play_variation(
        self,
        path: str,
        volume: float | None = None,
        timestamp: float | None = None,
        *,
        cooldown_ms: int | None = None,
    ) -> object:
        self.paths.append(path)
        self.timestamps.append(timestamp)
        return object()


def _make_player() -> Player:
    ball = cast(Ball, DummyBall())
    weapon = cast(Weapon, DummyWeapon())
    policy = cast(StatefulPolicy, DummyPolicy())
    audio = cast(BallAudio, DummyBallAudio())
    return Player(EntityId(1), ball, weapon, policy, (1.0, 0.0), (0, 0, 0), audio)


def test_dash_triggers_sound() -> None:
    player = _make_player()
    world = cast(PhysicsWorld, DummyWorld())
    renderer = cast(Renderer, SimpleNamespace())
    hud = cast(Hud, SimpleNamespace())
    engine = DummyEngine()
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
        cast(AudioEngine, engine),
        recorder,
        intro,
    )

    controller._update_players(0.0)

    path = Path("assets/dash.ogg").as_posix()
    assert path in engine.paths
    idx = engine.paths.index(path)
    assert engine.timestamps[idx] == 0.0
