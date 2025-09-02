from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

from app.ai.stateful_policy import StatefulPolicy
from app.audio import BallAudio
from app.core.types import Damage, EntityId
from app.game.controller import GameController, Player
from app.weapons.base import Weapon
from app.world.entities import Ball
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

    def dash_direction(self, _eid: EntityId, _view: object, _now: float, _can_dash: Any) -> None:
        return None


class DummyBallAudio:
    def on_hit(self, _timestamp: float | None = None) -> None:  # pragma: no cover - stub
        return

    def on_explode(self, _timestamp: float | None = None) -> None:  # pragma: no cover - stub
        return

    def stop_idle(self, _timestamp: float | None = None) -> None:  # pragma: no cover - stub
        return


class DummyBall:
    def __init__(self, x: float) -> None:
        self.body = Body(1.0, 0.0)
        self.body.position = (x, 0.0)
        self.body.velocity = (0.0, 0.0)
        self.shape = SimpleNamespace(radius=40.0)
        self.stats = SimpleNamespace(max_speed=100.0)
        self.health = 100.0

    def cap_speed(self) -> None:  # pragma: no cover - stub
        return

    def take_damage(self, damage: Damage) -> bool:
        self.health -= damage.amount
        return self.health <= 0


def _make_player(eid: int, x: float) -> Player:
    ball = cast(Ball, DummyBall(x))
    weapon = cast(Weapon, DummyWeapon())
    policy = cast(StatefulPolicy, DummyPolicy())
    audio = cast(BallAudio, DummyBallAudio())
    return Player(EntityId(eid), ball, weapon, policy, (1.0, 0.0), (0, 0, 0), audio)


def _make_controller(player_a: Player, player_b: Player) -> GameController:
    world = cast(Any, DummyWorld())
    renderer = cast(Any, SimpleNamespace())
    hud = cast(Any, SimpleNamespace())
    engine = cast(Any, SimpleNamespace(play_variation=lambda *a, **k: None))
    recorder = cast(Any, SimpleNamespace(add_frame=lambda *_a: None, close=lambda *_a, **_k: None))
    intro = cast(Any, SimpleNamespace())
    return GameController(
        "a",
        "b",
        [player_a, player_b],
        world,
        renderer,
        hud,
        engine,
        recorder,
        intro,
    )


def test_dash_collision_deals_damage_and_knockback() -> None:
    player_a = _make_player(1, 0.0)
    player_b = _make_player(2, 70.0)
    controller = _make_controller(player_a, player_b)
    player_a.dash.start((1.0, 0.0), 0.0)
    controller._update_players(0.0)
    assert player_b.ball.health == 95.0
    assert player_b.ball.body.velocity.x > 0.0
    assert player_a.dash.has_hit


def test_dash_damage_scales_with_speed() -> None:
    player_a = _make_player(1, 0.0)
    player_b = _make_player(2, 70.0)
    controller = _make_controller(player_a, player_b)
    player_a.dash.start((1.0, 0.0), 0.0)
    player_a.ball.body.velocity = (player_a.dash.speed / 2.0, 0.0)
    controller._resolve_dash_collision(player_a, 0.0)
    assert player_b.ball.health == 97.5


def test_dashing_player_can_be_damaged() -> None:
    player_a = _make_player(1, 0.0)
    player_b = _make_player(2, 200.0)
    controller = _make_controller(player_a, player_b)
    player_a.dash.start((1.0, 0.0), 0.0)
    controller.view.deal_damage(player_a.eid, Damage(10.0), 0.0)
    assert player_a.ball.health == 90.0
