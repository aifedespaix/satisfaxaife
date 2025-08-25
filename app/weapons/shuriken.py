from __future__ import annotations

from app.core.types import Damage, EntityId, Vec2

from . import weapon_registry
from .base import Weapon, WorldView


class Shuriken(Weapon):
    """Ranged projectile weapon."""

    def __init__(self) -> None:
        super().__init__(name="shuriken", cooldown=0.4, damage=Damage(10))

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:
        speed = 600.0
        velocity = (direction[0] * speed, direction[1] * speed)
        position = view.get_position(owner)
        view.spawn_projectile(
            owner,
            position,
            velocity,
            radius=8.0,
            damage=self.damage,
            knockback=120.0,
            ttl=0.8,
        )


weapon_registry.register("shuriken", Shuriken)
