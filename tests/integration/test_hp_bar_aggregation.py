from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

from app.ai.stateful_policy import StatefulPolicy
from app.audio import BallAudio
from app.core.types import Damage, EntityId, TeamId
from app.game.controller import GameController, Player
from app.weapons.base import Weapon
from app.world.entities import Ball
from pymunk import Body


class DummyBall:
    def __init__(self, x: float) -> None:
        self.body = Body(1.0, 0.0)
        self.body.position = (x, 0.0)
        self.body.velocity = (0.0, 0.0)
        self.shape = SimpleNamespace(radius=40.0)
        self.stats = SimpleNamespace(max_speed=100.0, max_health=100.0)
        self.health = 100.0

    def cap_speed(self) -> None:  # pragma: no cover - stub
        return None

    def take_damage(self, damage: Damage) -> bool:  # pragma: no cover - stub
        self.health -= damage.amount
        return self.health <= 0


def make_player(eid: int, x: float, team: int) -> Player:
    ball = cast(Ball, DummyBall(x))
    weapon = cast(Weapon, SimpleNamespace())
    policy = cast(StatefulPolicy, SimpleNamespace())
    audio = cast(BallAudio, SimpleNamespace())
    return Player(
        EntityId(eid),
        ball,
        weapon,
        policy,
        (1.0, 0.0),
        (0, 0, 0),
        TeamId(team),
        audio,
    )


class StubRenderer:
    """Renderer capturing health bar updates."""

    def __init__(self) -> None:
        self.hp_calls: list[tuple[float, float]] = []
        self.surface = SimpleNamespace()

    def clear(self) -> None:  # pragma: no cover - stub
        return None

    def draw_ball(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
        return None

    def draw_impacts(self) -> None:  # pragma: no cover - stub
        return None

    def draw_eyes(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
        return None

    def update_hp(self, hp_a: float, hp_b: float) -> None:
        self.hp_calls.append((hp_a, hp_b))

    def draw_hp(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
        return None

    def present(self) -> None:  # pragma: no cover - stub
        return None


class StubHud:
    """HUD stub ignoring draw calls."""

    def draw_title(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
        return None

    def draw_watermark(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
        return None


class StubWorld:
    def set_projectile_removed_callback(self, _cb: Any) -> None:  # pragma: no cover - stub
        return None


class StubEngine:
    def play_variation(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - stub
        return None

    def stop_all(self) -> None:  # pragma: no cover - stub
        return None

    def start_capture(self) -> None:  # pragma: no cover - stub
        return None

    def end_capture(self) -> None:  # pragma: no cover - stub
        return None


class StubRecorder:
    def add_frame(self, *_a: Any) -> None:  # pragma: no cover - stub
        return None

    def close(self, *_a: Any, **_k: Any) -> None:  # pragma: no cover - stub
        return None


def test_health_bar_aggregates_team_hp() -> None:
    p1 = make_player(1, x=0.0, team=0)
    p2 = make_player(2, x=0.0, team=0)
    p3 = make_player(3, x=0.0, team=1)
    p4 = make_player(4, x=0.0, team=1)
    p1.ball.health = 60.0
    p3.ball.health = 50.0

    renderer = StubRenderer()
    hud = StubHud()
    world = cast(Any, StubWorld())
    engine = cast(Any, StubEngine())
    recorder = cast(Any, StubRecorder())
    intro = cast(Any, SimpleNamespace())

    controller = GameController(
        "a",
        "b",
        [p1, p2, p3, p4],
        world,
        cast(Any, renderer),
        cast(Any, hud),
        engine,
        recorder,
        intro,
    )

    controller._render_frame()

    assert renderer.hp_calls
    hp_a, hp_b = renderer.hp_calls[-1]
    assert abs(hp_a - 0.8) < 1e-6
    assert abs(hp_b - 0.75) < 1e-6
