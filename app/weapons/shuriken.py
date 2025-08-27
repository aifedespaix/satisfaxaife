from __future__ import annotations

from app.core.types import Damage, EntityId, Vec2
from app.world.entities import DEFAULT_BALL_RADIUS

from . import weapon_registry
from .assets import load_weapon_sprite
from .base import Weapon, WorldView


class Shuriken(Weapon):
    """Ranged projectile weapon."""

    def __init__(self) -> None:
        super().__init__(name="shuriken", cooldown=0.4, damage=Damage(10), speed=600.0)
        self._radius = DEFAULT_BALL_RADIUS / 3.0
        sprite_size = self._radius * 2.0
        self._sprite = load_weapon_sprite("shuriken", max_dim=sprite_size)

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:
        velocity = (direction[0] * self.speed, direction[1] * self.speed)
        position = view.get_position(owner)
        view.spawn_projectile(
            owner,
            position,
            velocity,
            radius=self._radius,
            damage=self.damage,
            knockback=120.0,
            ttl=0.8,
            sprite=self._sprite,
            spin=12.0,
        )


weapon_registry.register("shuriken", Shuriken)
