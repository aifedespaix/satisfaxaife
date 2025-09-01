from __future__ import annotations

import random
from dataclasses import dataclass, field

from app.ai.stateful_policy import StatefulPolicy
from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import WeaponEffect, WorldView


@dataclass
class DummyView(WorldView):
    me: EntityId
    enemy: EntityId
    pos_me: Vec2
    pos_enemy: Vec2
    vel_enemy: Vec2 = (0.0, 0.0)
    projectiles: list[ProjectileInfo] = field(default_factory=list)

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.enemy

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.pos_me if eid == self.me else self.pos_enemy

    def get_velocity(self, eid: EntityId) -> Vec2:  # noqa: D401
        return (0.0, 0.0) if eid == self.me else self.vel_enemy

    def get_health_ratio(self, eid: EntityId) -> float:  # noqa: D401
        return 1.0

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:  # noqa: D401
        return None

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
        sprite: object | None = None,
        spin: float = 0.0,
        trail_color: tuple[int, int, int] | None = None,
        acceleration: float = 0.0,
    ) -> WeaponEffect:  # noqa: D401
        raise NotImplementedError

    def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:  # noqa: D401
        return self.projectiles


def _collect_faces(seed: int) -> list[Vec2]:
    rng = random.Random(seed)
    policy = StatefulPolicy("aggressive", rng=rng)
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (50.0, 0.0))
    faces: list[Vec2] = []
    for _ in range(3):
        _, face, _, _ = policy.decide(EntityId(1), view, 600.0)
        faces.append(face)
    return faces


def test_sequences_differ_with_seed() -> None:
    assert _collect_faces(1) != _collect_faces(2)


def _collect_dodges(seed: int) -> list[Vec2]:
    rng = random.Random(seed)
    policy = StatefulPolicy("aggressive", rng=rng)
    me = EntityId(1)
    enemy = EntityId(2)
    projectile = ProjectileInfo(owner=enemy, position=(50.0, 0.0), velocity=(-80.0, 0.0))
    view = DummyView(me, enemy, (0.0, 0.0), (100.0, 0.0), projectiles=[projectile])
    accels: list[Vec2] = []
    for _ in range(3):
        accel, _, _, _ = policy.decide(me, view, 600.0)
        accels.append(accel)
    return accels


def test_dodge_sequence_depends_on_seed() -> None:
    assert _collect_dodges(1) != _collect_dodges(2)
    assert _collect_dodges(3) == _collect_dodges(3)
