from dataclasses import dataclass, field

import pygame

from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import Weapon, WeaponEffect, WorldView
from app.weapons.effects import OrbitingSprite


@dataclass
class DummyView(WorldView):
    positions: dict[EntityId, Vec2]
    impulses: dict[EntityId, Vec2] = field(default_factory=dict)
    weapons: dict[EntityId, Weapon] = field(default_factory=dict)

    def get_enemy(self, owner: EntityId) -> EntityId | None:
        return None

    def get_position(self, eid: EntityId) -> Vec2:
        return self.positions[eid]

    def get_velocity(self, eid: EntityId) -> Vec2:
        return (0.0, 0.0)

    def get_health_ratio(self, eid: EntityId) -> float:
        return 1.0

    def get_team_color(self, eid: EntityId) -> tuple[int, int, int]:
        return (int(eid), 0, 0)

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:
        return None

    def heal(self, eid: EntityId, amount: float, timestamp: float) -> None:
        return None

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:
        self.impulses[eid] = (vx, vy)

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

    def get_weapon(self, eid: EntityId) -> Weapon:
        return self.weapons[eid]


def test_orbiting_sprite_applies_knockback() -> None:
    pygame.init()
    owner = EntityId(1)
    target = EntityId(2)
    positions = {owner: (0.0, 0.0), target: (20.0, 0.0)}
    view = DummyView(positions)
    sprite = pygame.Surface((10, 10))
    blade = OrbitingSprite(
        owner=owner,
        damage=Damage(0),
        sprite=sprite,
        radius=10.0,
        angle=0.0,
        speed=0.0,
        knockback=100.0,
    )
    blade.on_hit(view, target, timestamp=0.0)
    assert view.impulses[target] == (100.0, 0.0)
