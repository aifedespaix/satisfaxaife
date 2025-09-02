from __future__ import annotations

from dataclasses import dataclass, field

import pygame

from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import WeaponEffect, WorldView
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


@dataclass
class DummyView(WorldView):
    positions: dict[EntityId, Vec2]
    velocities: dict[EntityId, Vec2]
    enemies: dict[EntityId, EntityId]
    damage: dict[EntityId, float] = field(default_factory=dict)

    def get_enemy(self, owner: EntityId) -> EntityId | None:
        return self.enemies.get(owner)

    def get_position(self, eid: EntityId) -> Vec2:
        return self.positions[eid]

    def get_velocity(self, eid: EntityId) -> Vec2:
        return self.velocities.get(eid, (0.0, 0.0))

    def get_health_ratio(self, eid: EntityId) -> float:
        return 1.0

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:
        self.damage[eid] = self.damage.get(eid, 0.0) + damage.amount

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:
        return None

    def spawn_effect(self, effect: WeaponEffect) -> None:
        return None

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:
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
    ) -> WeaponEffect:
        raise NotImplementedError

    def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:
        return []


def test_projectile_collision_cooldown() -> None:
    pygame.init()
    world = PhysicsWorld()

    owner_a, owner_b = EntityId(1), EntityId(2)
    positions = {owner_a: (0.0, 0.0), owner_b: (100.0, 0.0)}
    velocities = {owner_a: (0.0, 0.0), owner_b: (0.0, 0.0)}
    enemies = {owner_a: owner_b, owner_b: owner_a}
    view = DummyView(positions, velocities, enemies)

    world.set_context(view, 0.0)
    proj_a = Projectile.spawn(
        world,
        owner=owner_a,
        position=(50.0, 0.0),
        velocity=(0.0, 0.0),
        radius=1.0,
        damage=Damage(1),
        knockback=0.0,
        ttl=1.0,
    )
    proj_b = Projectile.spawn(
        world,
        owner=owner_b,
        position=(50.0, 0.0),
        velocity=(0.0, 0.0),
        radius=1.0,
        damage=Damage(1),
        knockback=0.0,
        ttl=1.0,
    )
    world._index.rebuild()
    world._process_projectile_collisions()

    assert proj_a.owner == owner_b
    assert proj_b.owner == owner_a

    world.set_context(view, 0.5)
    world._index.rebuild()
    world._process_projectile_collisions()
    assert proj_a.owner == owner_b
    assert proj_b.owner == owner_a

    world.set_context(view, 1.1)
    world._index.rebuild()
    world._process_projectile_collisions()
    assert proj_a.owner == owner_a
    assert proj_b.owner == owner_b
