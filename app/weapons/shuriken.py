from __future__ import annotations

from app.core.types import Damage, EntityId, Vec2
from app.render.sprites import load_sprite

from . import weapon_registry
from .base import Weapon, WorldView


class Shuriken(Weapon):
    """Ranged projectile weapon."""

    def __init__(self) -> None:
        super().__init__(name="shuriken", cooldown=0.4, damage=Damage(10), speed=600.0)
        self._sprite = load_sprite("shuriken.png", scale=0.5)

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:
        velocity = (direction[0] * self.speed, direction[1] * self.speed)
        position = view.get_position(owner)
        view.spawn_projectile(
            owner,
            position,
            velocity,
            radius=8.0,
            damage=self.damage,
            knockback=120.0,
            ttl=0.8,
            sprite=self._sprite,
            spin=12.0,
        )


weapon_registry.register("shuriken", Shuriken)
