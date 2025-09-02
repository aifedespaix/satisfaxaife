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


class Knife(Weapon):
    """Fast orbiting blade that grants its wielder extra speed."""

    player_speed_bonus: float = 120.0
    range_type: RangeType = "contact"

    def __init__(self) -> None:
        super().__init__(
            name="knife",
            cooldown=0.0,
            damage=Damage(8),
            speed=12.0,
            range_type=self.range_type,
        )
        blade_height = DEFAULT_BALL_RADIUS * 2.0
        self._sprite = pygame.transform.rotate(
            load_weapon_sprite("knife", max_dim=blade_height),
            -90,
        )
        self.audio = WeaponAudio("melee", "knife")
        self._initialized = False
        self._boost_applied = False

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:  # noqa: D401
        return None

    def update(self, owner: EntityId, view: WorldView, dt: float) -> None:  # noqa: D401
        if not self._initialized:
            effect = OrbitingSprite(
                owner=owner,
                damage=self.damage,
                sprite=self._sprite,
                radius=60.0,
                angle=0.0,
                speed=self.speed,
                knockback=120.0,
                audio=self.audio,
            )
            view.spawn_effect(effect)
            self.audio.start_idle()
            self._initialized = True
        if not self._boost_applied:
            view.add_speed_bonus(owner, self.player_speed_bonus)
            self._boost_applied = True
        super().update(owner, view, dt)

    def parry(self, owner: EntityId, view: WorldView) -> None:  # noqa: D401
        effect = ParryEffect(owner=owner, radius=80.0, duration=0.15)
        view.spawn_effect(effect)


weapon_registry.register("knife", Knife)
