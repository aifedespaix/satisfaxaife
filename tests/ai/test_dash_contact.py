from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.ai.policy import SimplePolicy
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


def test_dash_does_not_retreat() -> None:
    """Dash direction never points away from the enemy."""

    me = EntityId(1)
    enemy = EntityId(2)
    proj = ProjectileInfo(owner=enemy, position=(0.0, -50.0), velocity=(0.0, 400.0))
    view = DummyView(me, enemy, (0.0, 0.0), (50.0, 0.0), [proj])
    policy = SimplePolicy("aggressive")

    direction = policy.dash_direction(me, view, 0.0, lambda _now: True)
    assert direction is not None
    forward = (1.0, 0.0)
    dot = direction[0] * forward[0] + direction[1] * forward[1]
    assert dot >= 0.0
    assert math.isclose(direction[0], forward[0])
    assert math.isclose(direction[1], forward[1])


def test_dash_reacts_to_projectile() -> None:
    """Dash vector keeps forward component while dodging laterally."""

    me = EntityId(1)
    enemy = EntityId(2)
    proj = ProjectileInfo(owner=enemy, position=(50.0, 100.0), velocity=(-400.0, -400.0))
    view = DummyView(me, enemy, (0.0, 0.0), (50.0, 0.0), [proj])
    policy = SimplePolicy("aggressive")

    direction = policy.dash_direction(me, view, 0.0, lambda _now: True)
    assert direction is not None
    forward = (1.0, 0.0)
    dot = direction[0] * forward[0] + direction[1] * forward[1]
    assert dot >= 0.0
    assert abs(direction[1]) > 0.0
