from dataclasses import dataclass, field
from typing import cast

import pygame

from app.audio.weapons import WeaponAudio
from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import Weapon, WeaponEffect, WorldView
from app.weapons.parry import ParryEffect
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


@dataclass
class DummyView(WorldView):
    positions: dict[EntityId, Vec2]
    velocities: dict[EntityId, Vec2]
    enemies: dict[EntityId, EntityId]
    weapons: dict[EntityId, Weapon] = field(default_factory=dict)
    parries: dict[EntityId, ParryEffect] = field(default_factory=dict)
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

    def get_weapon(self, eid: EntityId) -> Weapon:
        return self.weapons[eid]

    def get_parry(self, eid: EntityId) -> ParryEffect | None:
        return self.parries.get(eid)


class StubAudio:
    def __init__(self) -> None:
        self.throw_calls = 0
        self.touch_calls = 0

    def on_throw(self, timestamp: float | None = None) -> None:
        self.throw_calls += 1

    def on_touch(self, timestamp: float | None = None) -> None:
        self.touch_calls += 1


def test_crossing_projectiles_swap_owner_and_retarget() -> None:
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
        position=(0.0, 0.0),
        velocity=(100.0, 0.0),
        radius=1.0,
        damage=Damage(1),
        knockback=0.0,
        ttl=1.0,
    )
    proj_b = Projectile.spawn(
        world,
        owner=owner_b,
        position=(100.0, 0.0),
        velocity=(-100.0, 0.0),
        radius=1.0,
        damage=Damage(1),
        knockback=0.0,
        ttl=1.0,
    )

    audio_a, audio_b = StubAudio(), StubAudio()
    proj_a.audio = cast(WeaponAudio, audio_a)
    proj_b.audio = cast(WeaponAudio, audio_b)
    audio_a.on_throw()
    audio_b.on_throw()

    world.step(0.5)
    world._index.rebuild()
    world._process_projectile_collisions()

    assert proj_a.owner == owner_b
    assert proj_b.owner == owner_a
    assert proj_a.body.velocity.x < 0
    assert proj_b.body.velocity.x > 0
    assert audio_a.throw_calls == 1
    assert audio_b.throw_calls == 1
    assert audio_a.touch_calls == 1
    assert audio_b.touch_calls == 1
