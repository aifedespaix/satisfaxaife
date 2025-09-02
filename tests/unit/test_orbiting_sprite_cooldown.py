import math
from dataclasses import dataclass, field

import pygame

from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import WeaponEffect, WorldView
from app.weapons.effects import OrbitingSprite


@dataclass
class DummyView(WorldView):
    positions: dict[EntityId, Vec2]
    enemies: dict[EntityId, EntityId]
    damage: dict[EntityId, float] = field(default_factory=dict)

    def get_enemy(self, owner: EntityId) -> EntityId | None:
        return self.enemies.get(owner)

    def get_position(self, eid: EntityId) -> Vec2:
        return self.positions[eid]

    def get_velocity(self, eid: EntityId) -> Vec2:
        return (0.0, 0.0)

    def get_health_ratio(self, eid: EntityId) -> float:
        return 1.0

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:
        self.damage[eid] = self.damage.get(eid, 0.0) + damage.amount

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:
        return None

    def spawn_effect(self, effect: WeaponEffect) -> None:
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
    ) -> WeaponEffect:
        raise NotImplementedError

    def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:
        return []


def test_orbiting_sprite_requires_half_turn_between_hits() -> None:
    pygame.init()
    owner = EntityId(1)
    target = EntityId(2)
    positions = {owner: (0.0, 0.0), target: (10.0, 0.0)}
    enemies: dict[EntityId, EntityId] = {}
    view = DummyView(positions, enemies)
    sprite = pygame.Surface((20, 20))
    effect = OrbitingSprite(
        owner=owner,
        damage=Damage(5),
        sprite=sprite,
        radius=10.0,
        angle=0.0,
        speed=0.0,
    )

    effect.on_hit(view, target, timestamp=0.0)
    assert view.damage[target] == 5

    effect.angle = 0.1
    effect.on_hit(view, target, timestamp=0.1)
    assert view.damage[target] == 5

    effect.angle = math.pi
    effect.on_hit(view, target, timestamp=0.2)
    assert view.damage[target] == 10
