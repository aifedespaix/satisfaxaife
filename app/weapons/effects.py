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
from .utils import critical_multiplier


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
    thickness: float | None = None
    knockback: float = 0.0
    trail_color: Color = (255, 255, 255)
    trail: list[Vec2] = field(default_factory=list)
    trail_len: int = 8
    audio: WeaponAudio | None = None
    hit_angles: dict[EntityId, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.thickness is None:
            self.thickness = max(self.sprite.get_width(), self.sprite.get_height()) / 4

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
        owner_pos = view.get_position(self.owner)
        dx = owner_pos[0] - position[0]
        dy = owner_pos[1] - position[1]
        distance = math.hypot(dx, dy)
        thickness = self.thickness
        assert thickness is not None
        return abs(distance - self.radius) <= (thickness + radius)

    @staticmethod
    def _angle_distance(a: float, b: float) -> float:
        """Return the smallest absolute distance between angles ``a`` and ``b``."""
        return abs((a - b + math.pi) % tau - math.pi)

    def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool:  # noqa: D401
        """Apply damage if the blade rotated at least half a turn since the last hit."""
        last_angle = self.hit_angles.get(target)
        if last_angle is not None and self._angle_distance(self.angle, last_angle) < math.pi:
            return True
        mult = critical_multiplier(view, self.owner)
        view.deal_damage(target, Damage(self.damage.amount * mult), timestamp)
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


@dataclass(slots=True)
class GravityWellEffect(WeaponEffect):
    """Attracts entities toward a center point while dealing damage over time."""

    owner: EntityId
    position: Vec2
    radius: float
    pull_strength: float
    damage_per_second: float
    ttl: float
    _last_hit: dict[EntityId, float] = field(default_factory=dict)

    def step(self, dt: float) -> bool:
        """Decrease remaining lifetime and report whether the effect persists."""
        self.ttl -= dt
        return self.ttl > 0.0

    def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:
        """Return True if the circle at ``position`` intersects the well."""
        dx = self.position[0] - position[0]
        dy = self.position[1] - position[1]
        return dx * dx + dy * dy <= (self.radius + radius) ** 2

    def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool:
        """Pull ``target`` toward the center and apply continuous damage."""
        target_pos = view.get_position(target)
        dx = self.position[0] - target_pos[0]
        dy = self.position[1] - target_pos[1]
        distance = math.hypot(dx, dy) or 1.0
        nx = dx / distance
        ny = dy / distance
        view.apply_impulse(target, nx * self.pull_strength, ny * self.pull_strength)

        last = self._last_hit.get(target, timestamp)
        delta = timestamp - last
        if delta > 0.0:
            view.deal_damage(target, Damage(self.damage_per_second * delta), timestamp)
        self._last_hit[target] = timestamp
        return True

    def draw(self, renderer: Renderer, view: WorldView) -> None:
        """Render the gravitational field as a simple circle."""
        pygame.draw.circle(renderer.surface, (80, 80, 80), self.position, int(self.radius), 1)

    def destroy(self) -> None:
        """Clear cached hit timestamps."""
        self._last_hit.clear()


@dataclass(slots=True)
class ResonanceWaveEffect(WeaponEffect):
    """Expanding ring that reflects and amplifies on each bounce."""

    owner: EntityId
    position: Vec2
    max_radius: float
    speed: float
    damage: Damage
    amplification: float
    thickness: float = 4.0
    radius: float = 0.0
    direction: int = 1

    def step(self, dt: float) -> bool:
        """Update the wave radius and handle reflections."""
        self.radius += self.speed * dt * self.direction
        if self.radius >= self.max_radius:
            self.radius = self.max_radius
            self.direction = -1
            self.damage = Damage(self.damage.amount * self.amplification)
        elif self.radius <= 0.0 and self.direction < 0:
            return False
        return True

    def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:
        """Return True if the wave intersects a circle at ``position``."""
        dx = self.position[0] - position[0]
        dy = self.position[1] - position[1]
        distance = math.hypot(dx, dy)
        return abs(distance - self.radius) <= (self.thickness + radius)

    def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool:
        """Apply amplified damage to ``target``."""
        mult = critical_multiplier(view, self.owner)
        view.deal_damage(target, Damage(self.damage.amount * mult), timestamp)
        return True

    def draw(self, renderer: Renderer, view: WorldView) -> None:
        """Render the circular wave."""
        pygame.draw.circle(
            renderer.surface,
            (180, 180, 255),
            self.position,
            int(self.radius),
            int(self.thickness),
        )

    def destroy(self) -> None:
        """No resources to free."""
        return None
