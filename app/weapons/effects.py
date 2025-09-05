from __future__ import annotations

import math
from dataclasses import dataclass, field
from math import tau

import numpy as np
import pygame

from app.audio.weapons import WeaponAudio
from app.core.types import Color, Damage, EntityId, Vec2
from app.render.renderer import Renderer
from app.world.entities import DEFAULT_BALL_RADIUS
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
    hit_times: dict[EntityId, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.thickness is None:
            self.thickness = max(self.sprite.get_width(), self.sprite.get_height()) / 8

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
        inner = max(self.radius - thickness, 0.0)
        outer = self.radius + thickness
        if distance + radius < inner:
            return False
        if distance - radius > outer:
            return False
        return True

    def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool:  # noqa: D401
        """Apply damage if ``target`` was not hit during the last 0.1 s."""
        last = self.hit_times.get(target)
        if last is not None and timestamp - last < 0.1:
            return True
        owner_color = view.get_team_color(self.owner)
        target_color = view.get_team_color(target)
        mult = critical_multiplier(view, self.owner)
        amount = self.damage.amount * mult
        if owner_color == target_color:
            view.heal(target, amount, timestamp)
        else:
            view.deal_damage(target, Damage(amount), timestamp)
        blade_pos = self._position(view)
        target_pos = view.get_position(target)
        dx = target_pos[0] - blade_pos[0]
        dy = target_pos[1] - blade_pos[1]
        norm = math.hypot(dx, dy) or 1.0
        view.apply_impulse(target, dx / norm * self.knockback, dy / norm * self.knockback)
        if self.audio is not None:
            self.audio.on_touch(timestamp)
        self.hit_times[target] = timestamp
        return True

    def deflect_projectile(self, view: WorldView, projectile: Projectile, timestamp: float) -> None:
        """Reflect ``projectile`` toward the current enemy, unless it is allied."""
        if projectile.owner == self.owner:
            return None
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
        if renderer.debug:
            thickness = self.thickness or 0.0
            center = view.get_position(self.owner)
            renderer.draw_circle_outline(center, self.radius + thickness, (0, 255, 0))
            renderer.draw_circle_outline(center, max(self.radius - thickness, 0.0), (0, 255, 0))

    def destroy(self) -> None:  # noqa: D401
        self.trail.clear()


@dataclass(slots=True)
class OrbitingRectangle(WeaponEffect):
    """Rectangular blade rotating around its owner and dealing contact damage."""

    owner: EntityId
    damage: Damage
    width: float
    height: float
    offset: float
    angle: float
    speed: float
    knockback: float = 0.0
    audio: WeaponAudio | None = None
    hit_times: dict[EntityId, float] = field(default_factory=dict)
    sprite: pygame.Surface | None = None

    def __post_init__(self) -> None:
        if self.offset <= DEFAULT_BALL_RADIUS:
            msg = "offset must exceed DEFAULT_BALL_RADIUS to avoid owner's hitbox"
            raise ValueError(msg)

    def step(self, dt: float) -> bool:  # noqa: D401
        """Advance rotation angle by ``speed``."""
        self.angle = float(np.float32(self.angle + self.speed * dt) % np.float32(tau))
        return True

    def _center(self, view: WorldView) -> Vec2:
        owner_pos = view.get_position(self.owner)
        c, s = math.cos(self.angle), math.sin(self.angle)
        return (owner_pos[0] + c * self.offset, owner_pos[1] + s * self.offset)

    def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:  # noqa: D401
        """Return ``True`` if the circle at ``position`` intersects the blade."""
        center = self._center(view)
        theta = self.angle + math.pi / 2
        cos_t, sin_t = math.cos(theta), math.sin(theta)
        dx, dy = position[0] - center[0], position[1] - center[1]
        local_x = dx * cos_t + dy * sin_t
        local_y = -dx * sin_t + dy * cos_t
        half_w = self.width / 2
        half_h = self.height / 2
        closest_x = min(max(local_x, -half_w), half_w)
        closest_y = min(max(local_y, -half_h), half_h)
        dist_x = local_x - closest_x
        dist_y = local_y - closest_y
        return dist_x * dist_x + dist_y * dist_y <= radius * radius

    def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool:  # noqa: D401
        """Apply damage if ``target`` was not hit during the last 0.1 s."""
        last = self.hit_times.get(target)
        if last is not None and timestamp - last < 0.1:
            return True
        owner_color = view.get_team_color(self.owner)
        target_color = view.get_team_color(target)
        mult = critical_multiplier(view, self.owner)
        amount = self.damage.amount * mult
        if owner_color == target_color:
            view.heal(target, amount, timestamp)
        else:
            view.deal_damage(target, Damage(amount), timestamp)
        blade_pos = self._center(view)
        target_pos = view.get_position(target)
        dx = target_pos[0] - blade_pos[0]
        dy = target_pos[1] - blade_pos[1]
        norm = math.hypot(dx, dy) or 1.0
        view.apply_impulse(target, dx / norm * self.knockback, dy / norm * self.knockback)
        if self.audio is not None:
            self.audio.on_touch(timestamp)
        self.hit_times[target] = timestamp
        return True

    def deflect_projectile(self, view: WorldView, projectile: Projectile, timestamp: float) -> None:
        """Reflect ``projectile`` toward the current enemy, unless it is allied."""
        if projectile.owner == self.owner:
            return None
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
        center = self._center(view)
        if self.sprite is not None:
            renderer.draw_sprite(self.sprite, center, self.angle)
        if renderer.debug:
            c, s = math.cos(self.angle), math.sin(self.angle)
            tc, ts = -s, c
            hw, hh = self.width / 2, self.height / 2
            corners = [
                (center[0] + tc * hw + c * hh, center[1] + ts * hw + s * hh),
                (center[0] - tc * hw + c * hh, center[1] - ts * hw + s * hh),
                (center[0] - tc * hw - c * hh, center[1] - ts * hw - s * hh),
                (center[0] + tc * hw - c * hh, center[1] + ts * hw - s * hh),
            ]
            for a, b in zip(corners, corners[1:] + [corners[0]], strict=False):
                renderer.draw_line(a, b, (0, 255, 0))

    def destroy(self) -> None:  # noqa: D401
        return None


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
            owner_color = view.get_team_color(self.owner)
            target_color = view.get_team_color(target)
            amount = self.damage_per_second * delta
            if owner_color == target_color:
                view.heal(target, amount, timestamp)
            else:
                view.deal_damage(target, Damage(amount), timestamp)
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
        owner_color = view.get_team_color(self.owner)
        target_color = view.get_team_color(target)
        mult = critical_multiplier(view, self.owner)
        amount = self.damage.amount * mult
        if owner_color == target_color:
            view.heal(target, amount, timestamp)
        else:
            view.deal_damage(target, Damage(amount), timestamp)
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
