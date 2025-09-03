from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

import pygame

from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import Weapon, WeaponEffect, WorldView
from app.weapons.effects import OrbitingRectangle
from app.world.entities import DEFAULT_BALL_RADIUS, Ball
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


@dataclass
class DummyView(WorldView):
    """Minimal ``WorldView`` implementation for projectile tests."""

    positions: dict[EntityId, Vec2]
    weapons: dict[EntityId, Weapon]
    damage: dict[EntityId, float] = field(default_factory=dict)

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return None

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


class DummyContactWeapon:
    """Contact weapon stub tracking deflection calls."""

    range_type = "contact"

    def __init__(self) -> None:
        self.deflected = False

    def deflect_projectile(self, view: WorldView, projectile: Projectile, timestamp: float) -> None:  # noqa: D401
        self.deflected = True


def test_contact_weapon_body_hit_applies_damage() -> None:
    pygame.init()
    world = PhysicsWorld()
    owner_ball = Ball.spawn(world, (0.0, 0.0))
    owner = owner_ball.eid
    enemy = EntityId(2)
    weapon = DummyContactWeapon()
    positions = {owner: (0.0, 0.0), enemy: (100.0, 0.0)}
    view = DummyView(positions, {owner: cast(Weapon, weapon), enemy: cast(Weapon, object())})
    projectile = Projectile.spawn(
        world,
        owner=enemy,
        position=(0.0, 0.0),
        velocity=(0.0, 0.0),
        radius=1.0,
        damage=Damage(5),
        knockback=0.0,
        ttl=1.0,
    )
    world.set_context(view, 0.0)
    world.step(0.1)
    assert view.damage[owner] == 5
    assert weapon.deflected is False
    assert projectile.owner == enemy


def test_contact_weapon_hitbox_collision_deflects_projectile() -> None:
    pygame.init()
    world = PhysicsWorld()
    owner = EntityId(1)
    enemy = EntityId(2)
    positions = {owner: (0.0, 0.0), enemy: (100.0, 0.0)}
    weapon = DummyContactWeapon()
    view = DummyView(positions, {owner: cast(Weapon, weapon), enemy: cast(Weapon, object())})
    effect = OrbitingRectangle(
        owner=owner,
        damage=Damage(5),
        width=DEFAULT_BALL_RADIUS / 4.0,
        height=DEFAULT_BALL_RADIUS * 2.0,
        offset=DEFAULT_BALL_RADIUS * 2.0,
        angle=0.0,
        speed=0.0,
    )
    projectile = Projectile.spawn(
        world,
        owner=enemy,
        position=(effect.offset, 0.0),
        velocity=(-100.0, 0.0),
        radius=1.0,
        damage=Damage(5),
        knockback=0.0,
        ttl=1.0,
    )
    pos = (float(projectile.body.position.x), float(projectile.body.position.y))
    assert effect.collides(view, pos, float(projectile.shape.radius))
    effect.deflect_projectile(view, projectile, timestamp=0.0)
    assert projectile.owner == owner
    assert view.damage == {}


def test_contact_weapon_ignores_allied_projectile() -> None:
    pygame.init()
    world = PhysicsWorld()
    owner = EntityId(1)
    positions = {owner: (0.0, 0.0)}
    weapon = DummyContactWeapon()
    view = DummyView(positions, {owner: cast(Weapon, weapon)})
    effect = OrbitingRectangle(
        owner=owner,
        damage=Damage(5),
        width=DEFAULT_BALL_RADIUS / 4.0,
        height=DEFAULT_BALL_RADIUS * 2.0,
        offset=DEFAULT_BALL_RADIUS * 2.0,
        angle=0.0,
        speed=0.0,
    )
    projectile = Projectile.spawn(
        world,
        owner=owner,
        position=(effect.offset, 0.0),
        velocity=(-100.0, 0.0),
        radius=1.0,
        damage=Damage(5),
        knockback=0.0,
        ttl=1.0,
    )
    pos = (float(projectile.body.position.x), float(projectile.body.position.y))
    assert effect.collides(view, pos, float(projectile.shape.radius))
    effect.deflect_projectile(view, projectile, timestamp=0.0)
    assert projectile.owner == owner
    assert weapon.deflected is False


def test_allied_projectile_body_hit_is_ignored() -> None:
    pygame.init()
    world = PhysicsWorld()
    owner_ball = Ball.spawn(world, (0.0, 0.0))
    owner = owner_ball.eid
    weapon = DummyContactWeapon()
    positions = {owner: (0.0, 0.0)}
    view = DummyView(positions, {owner: cast(Weapon, weapon)})
    _projectile = Projectile.spawn(
        world,
        owner=owner,
        position=(0.0, 0.0),
        velocity=(0.0, 0.0),
        radius=1.0,
        damage=Damage(5),
        knockback=0.0,
        ttl=1.0,
    )
    world.set_context(view, 0.0)
    world.step(0.1)
    assert view.damage == {}
