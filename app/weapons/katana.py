from __future__ import annotations

from app.core.types import Damage, EntityId, Vec2
from app.render.sprites import load_sprite

from . import weapon_registry
from .base import Weapon, WorldView
from .effects import OrbitingSprite


class Katana(Weapon):
    """Orbiting blade rotating around the owner."""

    def __init__(self) -> None:
        super().__init__(name="katana", cooldown=0.0, damage=Damage(18), speed=4.0)
        self._initialized = False
        self._sprite = load_sprite("katana.png", scale=0.6)

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:
        return None

    def update(self, owner: EntityId, view: WorldView, dt: float) -> None:
        if not self._initialized:
            effect = OrbitingSprite(
                owner=owner,
                damage=self.damage,
                sprite=self._sprite,
                radius=60.0,
                angle=0.0,
                speed=self.speed,
            )
            view.spawn_effect(effect)
            self._initialized = True
        super().update(owner, view, dt)


weapon_registry.register("katana", Katana)
