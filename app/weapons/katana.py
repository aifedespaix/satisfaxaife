from __future__ import annotations

import pygame

from app.audio.weapons import WeaponAudio
from app.core.types import Damage, EntityId, Vec2
from app.world.entities import DEFAULT_BALL_RADIUS

from . import weapon_registry
from .assets import load_weapon_sprite
from .base import RangeType, Weapon, WorldView
from .effects import OrbitingSprite
from .parry import ParryEffect


class Katana(Weapon):
    """Orbiting blade rotating around the owner."""

    range_type: RangeType = "contact"

    def __init__(self) -> None:
        super().__init__(
            name="katana",
            cooldown=0.1,
            damage=Damage(7),
            speed=5.0,
            range_type=self.range_type,
        )
        self.audio = WeaponAudio("melee", "katana")
        self._initialized = False
        blade_height = DEFAULT_BALL_RADIUS * 3.0
        self._sprite = pygame.transform.rotate(
            load_weapon_sprite("katana", max_dim=blade_height),
            -90,
        )

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
                thickness=self._sprite.get_width() / 2.0,
                knockback=220.0,
                audio=self.audio,
            )
            view.spawn_effect(effect)
            self.audio.start_idle()
            self._initialized = True
        super().update(owner, view, dt)

    def parry(self, owner: EntityId, view: WorldView) -> None:  # noqa: D401
        effect = ParryEffect(owner=owner, radius=80.0, duration=0.15)
        view.spawn_effect(effect)


weapon_registry.register("katana", Katana)
