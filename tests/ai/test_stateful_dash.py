from __future__ import annotations

import math
from dataclasses import dataclass, field

import pytest

from app.ai.stateful_policy import StatefulPolicy
from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import Weapon, WeaponEffect, WorldView


@dataclass
class DummyView(WorldView):
    """Minimal :class:`WorldView` providing projectile data for dash tests."""

    me: EntityId
    enemy: EntityId
    pos_me: Vec2
    pos_enemy: Vec2
    projectiles: list[ProjectileInfo] = field(default_factory=list)

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.enemy

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.pos_me if eid == self.me else self.pos_enemy

    def get_velocity(self, eid: EntityId) -> Vec2:  # pragma: no cover - unused
        return (0.0, 0.0)

    def get_health_ratio(self, eid: EntityId) -> float:  # pragma: no cover - unused
        return 1.0

    def deal_damage(
        self, eid: EntityId, damage: Damage, timestamp: float
    ) -> None:  # pragma: no cover - unused
        return None

    def apply_impulse(
        self, eid: EntityId, vx: float, vy: float
    ) -> None:  # pragma: no cover - unused
        return None

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # pragma: no cover - unused
        return None

    def spawn_effect(self, effect: WeaponEffect) -> None:  # pragma: no cover - unused
        return None

    def spawn_projectile(
        self,
        owner: EntityId,
        position: Vec2,
        velocity: Vec2,
        radius: float,
        damage: Damage,
        knockback: float,
        ttl: float,
        sprite: object | None = None,
        spin: float = 0.0,
        trail_color: tuple[int, int, int] | None = None,
        acceleration: float = 0.0,
    ) -> WeaponEffect:  # pragma: no cover - unused
        raise NotImplementedError

    def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:  # noqa: D401
        return [p for p in self.projectiles if p.owner != excluding]

    def get_weapon(self, eid: EntityId) -> Weapon:  # pragma: no cover - unused
        raise KeyError


def test_offensive_dash_forward_when_in_range() -> None:
    """Enemy within dash reach yields a straight forward dash."""

    me = EntityId(1)
    enemy = EntityId(2)
    proj = ProjectileInfo(owner=enemy, position=(0.0, 50.0), velocity=(0.0, -400.0))
    view = DummyView(me, enemy, (0.0, 0.0), (100.0, 0.0), [proj])
    policy = StatefulPolicy("aggressive", range_type="contact", transition_time=0.0)

    direction = policy.dash_direction(me, view, 0.1, lambda _now: True)
    assert direction is not None
    assert math.isclose(direction[0], 1.0)
    assert math.isclose(direction[1], 0.0)


def test_offensive_dash_diagonal_out_of_range() -> None:
    """Out-of-range targets produce a diagonal forward dash."""

    me = EntityId(1)
    enemy = EntityId(2)
    view = DummyView(me, enemy, (0.0, 0.0), (300.0, 0.0))
    policy = StatefulPolicy("aggressive", range_type="contact", transition_time=0.0)

    direction = policy.dash_direction(me, view, 0.1, lambda _now: True)
    assert direction is not None
    forward = (1.0, 0.0)
    dot = direction[0] * forward[0] + direction[1] * forward[1]
    assert dot > 0.0
    assert abs(direction[1]) > 0.0


@pytest.mark.parametrize("with_projectile", [False, True])
def test_defensive_dash_is_sideways(with_projectile: bool) -> None:
    """Defensive mode always dashes sideways, ignoring projectile threats."""

    me = EntityId(1)
    enemy = EntityId(2)
    projs = (
        [ProjectileInfo(owner=enemy, position=(0.0, -50.0), velocity=(0.0, 400.0))]
        if with_projectile
        else []
    )
    view = DummyView(me, enemy, (0.0, 0.0), (200.0, 0.0), projs)
    policy = StatefulPolicy("aggressive", range_type="contact", transition_time=1.0)

    direction = policy.dash_direction(me, view, 0.0, lambda _now: True)
    assert direction is not None
    forward = (1.0, 0.0)
    dot = direction[0] * forward[0] + direction[1] * forward[1]
    assert math.isclose(dot, 0.0)
    assert abs(direction[1]) > 0.0
