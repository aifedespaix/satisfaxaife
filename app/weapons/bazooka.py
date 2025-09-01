from __future__ import annotations

import math
from typing import cast

from app.core.types import Damage, EntityId, Vec2
from app.render.sprites import load_sprite
from app.world.entities import DEFAULT_BALL_RADIUS
from app.world.projectiles import Projectile

from . import weapon_registry
from .assets import load_weapon_sprite
from .base import Weapon, WorldView
from .effects import AimedSprite


class Bazooka(Weapon):
    """AI-controlled launcher that fires slow, heavy missiles."""

    missile_radius: float

    def __init__(self) -> None:
        super().__init__(name="bazooka", cooldown=1.2, damage=Damage(20), speed=300.0)
        weapon_size = DEFAULT_BALL_RADIUS * 2.0
        self._sprite = load_weapon_sprite("bazooka", max_dim=weapon_size)
        self._effect: AimedSprite | None = None
        self.missile_radius = DEFAULT_BALL_RADIUS / 2.0
        missile_size = self.missile_radius * 2.0
        self._missile_sprite = load_sprite("weapons/bazooka/missile.png", max_dim=missile_size)

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:  # noqa: D401
        velocity = (direction[0] * self.speed, direction[1] * self.speed)
        position = view.get_position(owner)
        proj = cast(
            Projectile,
            view.spawn_projectile(
                owner,
                position,
                velocity,
                radius=self.missile_radius,
                damage=self.damage,
                knockback=200.0,
                ttl=1.5,
                sprite=self._missile_sprite,
                trail_color=(255, 200, 50),
            ),
        )
        proj.angle = math.atan2(direction[1], direction[0]) + math.pi / 2

    def update(self, owner: EntityId, view: WorldView, dt: float) -> None:  # noqa: D401
        if self._effect is None:
            effect = AimedSprite(owner=owner, sprite=self._sprite, offset=DEFAULT_BALL_RADIUS * 1.5)
            view.spawn_effect(effect)
            self._effect = effect
        enemy = view.get_enemy(owner)
        if enemy is not None:
            target = view.get_position(enemy)
            origin = view.get_position(owner)
            dx, dy = target[0] - origin[0], target[1] - origin[1]
            angle = math.atan2(dy, dx)
            if self._effect is not None:
                self._effect.angle = angle
            if self._timer <= 0.0:
                norm = math.hypot(dx, dy) or 1.0
                direction = (dx / norm, dy / norm)
                self._fire(owner, view, direction)
                self._timer = self.cooldown
        super().update(owner, view, dt)


weapon_registry.register("bazooka", Bazooka)
