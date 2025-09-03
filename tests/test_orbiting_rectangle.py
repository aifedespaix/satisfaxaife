from __future__ import annotations

from types import SimpleNamespace
from typing import cast

from app.core.types import Damage, EntityId, Vec2
from app.weapons.base import WorldView
from app.weapons.effects import OrbitingRectangle
from app.world.entities import DEFAULT_BALL_RADIUS
from app.world.projectiles import Projectile


class DummyView:
    def __init__(self, positions: dict[EntityId, Vec2], enemy: EntityId | None = None) -> None:
        self._positions = positions
        self._enemy = enemy
        self.damage: dict[EntityId, float] = {}

    def get_position(self, eid: EntityId) -> Vec2:
        return self._positions[eid]

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self._enemy

    def get_weapon(self, eid: EntityId) -> object:  # pragma: no cover - unused
        raise NotImplementedError

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:
        self.damage[eid] = self.damage.get(eid, 0.0) + damage.amount

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
        return None


class DummyProjectile:
    def __init__(self, velocity: Vec2) -> None:
        self.body = SimpleNamespace(velocity=velocity)
        self.owner = EntityId(0)
        self.ttl = 1.0
        self.max_ttl = 2.0
        self.audio = None
        self.retarget_args: tuple[Vec2, EntityId] | None = None

    def retarget(self, target: Vec2, new_owner: EntityId) -> None:  # noqa: D401
        self.retarget_args = (target, new_owner)


def test_orbiting_rectangle_collides() -> None:
    owner = EntityId(1)
    effect = OrbitingRectangle(
        owner=owner,
        damage=Damage(1.0),
        width=20.0,
        height=40.0,
        offset=DEFAULT_BALL_RADIUS + 10.0,
        angle=0.0,
        speed=0.0,
    )
    view = cast(WorldView, DummyView({owner: (0.0, 0.0)}))
    assert effect.collides(view, (effect.offset, 0.0), 5.0)
    assert not effect.collides(view, (0.0, 0.0), 5.0)


def test_orbiting_rectangle_deflect_projectile() -> None:
    owner = EntityId(1)
    enemy = EntityId(2)
    effect = OrbitingRectangle(
        owner=owner,
        damage=Damage(1.0),
        width=20.0,
        height=40.0,
        offset=DEFAULT_BALL_RADIUS + 10.0,
        angle=0.0,
        speed=0.0,
    )
    view = cast(WorldView, DummyView({owner: (0.0, 0.0), enemy: (100.0, 0.0)}, enemy))
    projectile = DummyProjectile((1.0, 0.0))
    effect.deflect_projectile(view, cast(Projectile, projectile), 0.0)
    assert projectile.retarget_args == ((100.0, 0.0), owner)

    view_no_enemy = cast(WorldView, DummyView({owner: (0.0, 0.0)}, None))
    projectile2 = DummyProjectile((1.0, 2.0))
    effect.deflect_projectile(view_no_enemy, cast(Projectile, projectile2), 0.0)
    assert projectile2.body.velocity == (-1.0, -2.0)
    assert projectile2.owner == owner
    assert projectile2.ttl == projectile2.max_ttl


def test_orbiting_rectangle_respects_per_target_cooldown() -> None:
    owner = EntityId(1)
    target = EntityId(2)
    effect = OrbitingRectangle(
        owner=owner,
        damage=Damage(5),
        width=20.0,
        height=40.0,
        offset=DEFAULT_BALL_RADIUS + 10.0,
        angle=0.0,
        speed=0.0,
    )
    view_obj = DummyView({owner: (0.0, 0.0), target: (effect.offset, 0.0)})
    view = cast(WorldView, view_obj)

    effect.on_hit(view, target, timestamp=0.0)
    assert view_obj.damage[target] == 5

    effect.on_hit(view, target, timestamp=0.05)
    assert view_obj.damage[target] == 5

    effect.on_hit(view, target, timestamp=0.15)
    assert view_obj.damage[target] == 10
