from __future__ import annotations

from dataclasses import dataclass, field
from math import tau

import numpy as np
import pygame

from app.audio.weapons import WeaponAudio
from app.core.types import Color, Damage, EntityId, Vec2
from app.render.renderer import Renderer

from .base import WeaponEffect, WorldView


@dataclass(slots=True)
class OrbitingSprite(WeaponEffect):
    """Sprite rotating around its owner and applying damage on contact."""

    owner: EntityId
    damage: Damage
    sprite: pygame.Surface
    radius: float
    angle: float
    speed: float
    trail_color: Color = (255, 255, 255)
    trail: list[Vec2] = field(default_factory=list)
    trail_len: int = 8
    audio: WeaponAudio | None = None

    def step(self, dt: float) -> bool:  # noqa: D401
        self.angle = float(np.float32(self.angle + self.speed * dt) % np.float32(tau))
        return True

    def _position(self, view: WorldView) -> Vec2:
        center = view.get_position(self.owner)
        ang = np.float32(self.angle)
        c, s = float(np.cos(ang)), float(np.sin(ang))
        return (center[0] + c * self.radius, center[1] + s * self.radius)

    def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:  # noqa: D401
        cx, cy = self._position(view)
        dx, dy = cx - position[0], cy - position[1]
        hit_rad = max(self.sprite.get_width(), self.sprite.get_height()) / 2
        return bool(dx * dx + dy * dy <= (hit_rad + radius) ** 2)

    def on_hit(self, view: WorldView, target: EntityId) -> bool:  # noqa: D401
        view.deal_damage(target, self.damage)
        if self.audio is not None:
            self.audio.on_touch()
        return True

    def draw(self, renderer: Renderer, view: WorldView) -> None:  # noqa: D401
        pos = self._position(view)
        self.trail.append(pos)
        if len(self.trail) > self.trail_len:
            self.trail.pop(0)
        for a, b in zip(self.trail, self.trail[1:], strict=False):
            renderer.draw_line(a, b, self.trail_color, 2)
        renderer.draw_sprite(self.sprite, pos, self.angle)

    def destroy(self) -> None:  # noqa: D401
        self.trail.clear()
