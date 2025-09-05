"""Utility classes and helpers for tests."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pygame

from app.ai.stateful_policy import StatefulPolicy
from app.audio import BallAudio
from app.core.types import Damage, EntityId, ProjectileInfo, TeamId, Vec2
from app.game.controller import GameController, Player
from app.weapons.base import Weapon, WeaponEffect, WorldView
from app.world.entities import Ball
from pymunk import Body


class StubWorldView(WorldView):
    """Minimal :class:`WorldView` implementation for physics tests."""

    def __init__(self, ball: Ball) -> None:
        self.ball = ball

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # pragma: no cover - unused
        return None

    def get_position(self, eid: EntityId) -> Vec2:
        pos = self.ball.body.position
        return (float(pos.x), float(pos.y))

    def get_velocity(self, eid: EntityId) -> Vec2:  # pragma: no cover - unused
        return (0.0, 0.0)

    def get_health_ratio(self, eid: EntityId) -> float:  # pragma: no cover - unused
        return 1.0

    def get_team_color(self, eid: EntityId) -> tuple[int, int, int]:  # pragma: no cover - simple
        return (int(eid), 0, 0)

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:
        self.ball.take_damage(damage)

    def heal(self, eid: EntityId, amount: float, timestamp: float) -> None:  # pragma: no cover - unused
        self.ball.heal(amount)

    def apply_impulse(
        self, eid: EntityId, vx: float, vy: float
    ) -> None:  # pragma: no cover - unused
        self.ball.body.apply_impulse_at_local_point((vx, vy))

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # pragma: no cover - unused
        pass

    def spawn_effect(self, effect: WeaponEffect) -> None:  # pragma: no cover - unused
        pass

    def spawn_projectile(
        self,
        owner: EntityId,
        position: Vec2,
        velocity: Vec2,
        radius: float,
        damage: Damage,
        knockback: float,
        ttl: float,
        sprite: pygame.Surface | None = None,
        spin: float = 0.0,
        trail_color: tuple[int, int, int] | None = None,
        acceleration: float = 0.0,
    ) -> WeaponEffect:  # pragma: no cover - unused
        raise NotImplementedError

    def iter_projectiles(
        self, excluding: EntityId | None = None
    ) -> list[ProjectileInfo]:  # pragma: no cover - unused
        return []

    def get_weapon(self, eid: EntityId) -> Weapon:  # pragma: no cover - unused
        raise NotImplementedError


class DummyWorld:
    """Physics-free world stub used in unit tests."""

    def set_projectile_removed_callback(self, _cb: Any) -> None:
        return None

    def set_context(self, _view: object, _timestamp: float) -> None:  # pragma: no cover - stub
        return None

    def step(self, _dt: float, _substeps: int) -> None:  # pragma: no cover - stub
        return None


class DummyWeapon:
    """Weapon stub without any behaviour."""

    speed: float = 0.0

    def step(self, _dt: float) -> None:  # pragma: no cover - stub
        return None

    def update(
        self, _owner: EntityId, _view: object, _dt: float
    ) -> None:  # pragma: no cover - stub
        return None

    def trigger(
        self, _owner: EntityId, _view: object, _direction: tuple[float, float]
    ) -> None:  # pragma: no cover - stub
        return None


class DummyPolicy:
    """Policy stub returning fixed decisions."""

    def decide(
        self, _eid: EntityId, _view: object, _speed: float
    ) -> tuple[tuple[float, float], tuple[float, float], bool]:
        return (0.0, 0.0), (1.0, 0.0), False

    def dash_direction(self, _eid: EntityId, _view: object, _now: float, _can_dash: Any) -> None:
        return None


class DummyBallAudio:
    """Audio stub for ball-related sounds."""

    def on_hit(self, _timestamp: float | None = None) -> None:  # pragma: no cover - stub
        return None

    def on_explode(self, _timestamp: float | None = None) -> None:  # pragma: no cover - stub
        return None

    def stop_idle(self, _timestamp: float | None = None, *, disable: bool = False) -> None:  # pragma: no cover - stub
        return None


class DummyBall:
    """Simplified ball used in controller tests."""

    def __init__(self, x: float) -> None:
        self.body = Body(1.0, 0.0)
        self.body.position = (x, 0.0)
        self.body.velocity = (0.0, 0.0)
        self.shape = SimpleNamespace(radius=40.0)
        self.stats = SimpleNamespace(max_speed=100.0)
        self.health = 100.0

    def cap_speed(self) -> None:  # pragma: no cover - stub
        return None

    def take_damage(self, damage: Damage) -> bool:
        self.health -= damage.amount
        return self.health <= 0


def make_player(eid: int, x: float, team: int = 0) -> Player:
    """Return a :class:`Player` positioned at ``x`` with inert weapon."""

    ball = cast(Ball, DummyBall(x))
    weapon = cast(Weapon, DummyWeapon())
    policy = cast(StatefulPolicy, DummyPolicy())
    audio = cast(BallAudio, DummyBallAudio())
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


def make_controller(player_a: Player, player_b: Player) -> GameController:
    """Create a :class:`GameController` for unit tests."""

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
