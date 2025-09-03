from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import Weapon, WeaponEffect, WorldView
from app.weapons.effects import OrbitingSprite


@dataclass
class DummyView(WorldView):
    owner: EntityId
    target: EntityId
    last_damage: float = field(default=0.0, init=False)
    weapons: dict[EntityId, Weapon] = field(default_factory=dict)

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.target if owner == self.owner else self.owner

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return (0.0, 0.0)

    def get_velocity(self, eid: EntityId) -> Vec2:  # noqa: D401
        return (800.0, 0.0) if eid == self.owner else (0.0, 0.0)

    def get_health_ratio(self, eid: EntityId) -> float:  # noqa: D401
        return 1.0

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:  # noqa: D401
        self.last_damage = damage.amount

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
        return

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # noqa: D401
        return

    def spawn_effect(self, effect: WeaponEffect) -> None:  # noqa: D401
        return

    def spawn_projectile(self, *args: Any, **kwargs: Any) -> WeaponEffect:  # noqa: D401
        raise NotImplementedError

    def iter_projectiles(self, excluding: EntityId | None = None) -> Iterable[ProjectileInfo]:  # noqa: D401
        return []

    def get_weapon(self, eid: EntityId) -> Weapon:  # noqa: D401
        return self.weapons[eid]


def test_orbiting_sprite_deals_critical_damage_when_owner_is_fast() -> None:
    owner = EntityId(1)
    target = EntityId(2)
    view = DummyView(owner, target)
    sprite = SimpleNamespace(get_width=lambda: 10, get_height=lambda: 10)
    effect = OrbitingSprite(
        owner=owner,
        damage=Damage(7.0),
        sprite=sprite,
        radius=10.0,
        angle=0.0,
        speed=0.0,
        knockback=0.0,
    )
    effect.on_hit(view, target, 0.0)
    assert view.last_damage == 14.0
