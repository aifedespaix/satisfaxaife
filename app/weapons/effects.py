from __future__ import annotations

import math
from dataclasses import dataclass, field
from math import tau

import numpy as np
import pygame

from app.audio.weapons import WeaponAudio
from app.core.types import Color, Damage, EntityId, Vec2
from app.render.renderer import Renderer
from app.world.projectiles import Projectile

from .base import WeaponEffect, WorldView


@dataclass(slots=True)
class HeldSprite(WeaponEffect):
    """Static sprite following its owner without interacting with the world."""

    owner: EntityId
    sprite: pygame.Surface
    angle: float = 0.0

    def step(self, dt: float) -> bool:  # noqa: D401
        return True

    def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:  # noqa: D401
        return False

    def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool:  # noqa: D401
        return True

    def draw(self, renderer: Renderer, view: WorldView) -> None:  # noqa: D401
        pos = view.get_position(self.owner)
        renderer.draw_sprite(self.sprite, pos, self.angle)

    def destroy(self) -> None:  # noqa: D401
        return None


@dataclass(slots=True)
class AimedSprite(WeaponEffect):
    """Sprite attached to its owner and aligned with a given angle."""

    owner: EntityId
    sprite: pygame.Surface
    offset: float
    angle: float = 0.0

    def step(self, dt: float) -> bool:  # noqa: D401
        return True

    def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:  # noqa: D401
        return False

    def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool:  # noqa: D401
        return True

    def draw(self, renderer: Renderer, view: WorldView) -> None:  # noqa: D401
        center = view.get_position(self.owner)
        pos = (
            center[0] + math.cos(self.angle) * self.offset,
            center[1] + math.sin(self.angle) * self.offset,
        )
        renderer.draw_sprite(self.sprite, pos, self.angle)

    def destroy(self) -> None:  # noqa: D401
        return None


@dataclass(slots=True)
class OrbitingSprite(WeaponEffect):
    """Sprite rotating around its owner and applying damage on contact."""

    owner: EntityId
    damage: Damage
    sprite: pygame.Surface
    radius: float
    angle: float
    speed: float
    knockback: float = 0.0
    trail_color: Color = (255, 255, 255)
    trail: list[Vec2] = field(default_factory=list)
    trail_len: int = 8
    audio: WeaponAudio | None = None
    hit_angles: dict[EntityId, float] = field(default_factory=dict)

    def step(self, dt: float) -> bool:  # noqa: D401
        """Advance rotation."""
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

    @staticmethod
    def _angle_distance(a: float, b: float) -> float:
        """Return the smallest absolute distance between angles ``a`` and ``b``."""
        return abs((a - b + math.pi) % tau - math.pi)

    def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool:  # noqa: D401
        """Apply damage if the blade rotated at least half a turn since the last hit."""
        last_angle = self.hit_angles.get(target)
        if last_angle is not None and self._angle_distance(self.angle, last_angle) < math.pi:
            return True
        view.deal_damage(target, self.damage, timestamp)
        blade_pos = self._position(view)
        target_pos = view.get_position(target)
        dx = target_pos[0] - blade_pos[0]
        dy = target_pos[1] - blade_pos[1]
        norm = math.hypot(dx, dy) or 1.0
        view.apply_impulse(target, dx / norm * self.knockback, dy / norm * self.knockback)
        if self.audio is not None:
            self.audio.on_touch(timestamp)
        self.hit_angles[target] = self.angle
        return True

    def deflect_projectile(self, view: WorldView, projectile: Projectile, timestamp: float) -> None:
        """Reflect ``projectile`` and aim it at the current enemy."""
        enemy = view.get_enemy(self.owner)
        if enemy is not None:
            target = view.get_position(enemy)
            projectile.retarget(target, self.owner)
        else:
            vx, vy = projectile.body.velocity
            projectile.body.velocity = (-vx, -vy)
            projectile.owner = self.owner
            projectile.ttl = projectile.max_ttl
        if projectile.audio is not None:
            projectile.audio.on_touch(timestamp)

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
