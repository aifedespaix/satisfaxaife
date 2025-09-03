"""Verify knife's deflection and contact mechanics."""

# ruff: noqa: I001

from __future__ import annotations

import pathlib
import sys
from dataclasses import dataclass, field

import pygame

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import Weapon, WeaponEffect, WorldView
from app.weapons.effects import OrbitingRectangle
from app.world.entities import DEFAULT_BALL_RADIUS
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


@dataclass
class DummyView(WorldView):
    """Minimal :class:`WorldView` used for knife tests."""

    positions: dict[EntityId, Vec2]
    enemies: dict[EntityId, EntityId]
    weapons: dict[EntityId, Weapon] = field(default_factory=dict)
    damage: dict[EntityId, float] = field(default_factory=dict)

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.enemies.get(owner)

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.positions[eid]

    def get_velocity(self, eid: EntityId) -> Vec2:  # noqa: D401
        return (0.0, 0.0)

    def get_health_ratio(self, eid: EntityId) -> float:  # noqa: D401
        return 1.0

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:  # noqa: D401
        self.damage[eid] = self.damage.get(eid, 0.0) + damage.amount

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
        return None

    def spawn_effect(self, effect: WeaponEffect) -> None:  # noqa: D401
        return None

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # noqa: D401
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
        sprite: pygame.Surface | None = None,
        spin: float = 0.0,
        trail_color: tuple[int, int, int] | None = None,
        acceleration: float = 0.0,
    ) -> WeaponEffect:  # noqa: D401
        raise NotImplementedError

    def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:  # noqa: D401
        return []

    def get_weapon(self, eid: EntityId) -> Weapon:  # noqa: D401
        return self.weapons[eid]


def _make_knife(owner: EntityId) -> OrbitingRectangle:
    height = DEFAULT_BALL_RADIUS * 2.0
    width = DEFAULT_BALL_RADIUS / 4.0
    offset = DEFAULT_BALL_RADIUS + height / 2 + 1.0
    return OrbitingRectangle(
        owner=owner,
        damage=Damage(5),
        width=width,
        height=height,
        offset=offset,
        angle=0.0,
        speed=0.0,
    )


def test_knife_deflects_projectile() -> None:
    pygame.init()
    world = PhysicsWorld()
    owner = EntityId(1)
    enemy = EntityId(2)
    positions = {owner: (0.0, 0.0), enemy: (150.0, 0.0)}
    enemies = {owner: enemy, enemy: owner}
    view = DummyView(positions, enemies)
    knife = _make_knife(owner)
    projectile = Projectile.spawn(
        world,
        owner=enemy,
        position=(knife.offset, 0.0),
        velocity=(-100.0, 0.0),
        radius=1.0,
        damage=Damage(5),
        knockback=0.0,
        ttl=1.0,
    )
    projectile.ttl = 0.1
    pos = (float(projectile.body.position.x), float(projectile.body.position.y))
    assert knife.collides(view, pos, float(projectile.shape.radius))

    knife.deflect_projectile(view, projectile, timestamp=0.0)

    assert projectile.owner == owner
    assert projectile.body.velocity.x == 100.0
    assert projectile.ttl == projectile.max_ttl
    assert view.damage == {}

    projectile.on_hit(view, enemy, timestamp=0.1)
    assert view.damage[enemy] == 5


def test_knife_hits_enemy_ball() -> None:
    pygame.init()
    owner = EntityId(1)
    enemy = EntityId(2)
    height = DEFAULT_BALL_RADIUS * 2.0
    width = DEFAULT_BALL_RADIUS / 4.0
    offset = DEFAULT_BALL_RADIUS + height / 2 + 1.0
    positions = {owner: (0.0, 0.0), enemy: (offset, 0.0)}
    enemies = {owner: enemy, enemy: owner}
    view = DummyView(positions, enemies)
    knife = OrbitingRectangle(
        owner=owner,
        damage=Damage(5),
        width=width,
        height=height,
        offset=offset,
        angle=0.0,
        speed=0.0,
    )
    assert knife.collides(view, positions[enemy], DEFAULT_BALL_RADIUS)

    knife.on_hit(view, enemy, timestamp=0.0)

    assert view.damage[enemy] == 5
