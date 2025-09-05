from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from itertools import pairwise
from math import atan2, pi, sqrt
from typing import TYPE_CHECKING, cast

import pymunk
from app.core.types import Color, Damage, EntityId, Vec2
from app.weapons.base import WeaponEffect, WorldView
from app.weapons.utils import critical_multiplier
from app.world.physics import PhysicsWorld
from pymunk import Vec2 as Vec2d

if TYPE_CHECKING:
    import pygame

    from app.audio.weapons import WeaponAudio
from app.render.renderer import Renderer

PROJECTILE_COLLISION_TYPE: int = 2
"""Pymunk collision type value for projectile shapes."""


@dataclass(slots=True)
class Projectile(WeaponEffect):
    """Dynamic projectile with a limited lifetime."""

    world: PhysicsWorld
    owner: EntityId
    body: pymunk.Body
    shape: pymunk.Circle
    damage: Damage
    knockback: float
    ttl: float
    max_ttl: float
    sprite: pygame.Surface | None = None
    angle: float = 0.0
    spin: float = 0.0
    audio: WeaponAudio | None = None
    trail_color: Color | None = None
    trail: deque[Vec2] = field(default_factory=lambda: deque(maxlen=8))
    trail_width: int = 2
    acceleration: float = 0.0
    bounces: int = 0
    last_velocity: Vec2d = field(default_factory=lambda: Vec2d(0.0, 0.0))
    destroyed: bool = False

    @classmethod
    def spawn(
        cls,
        world: PhysicsWorld,
        owner: EntityId,
        position: Vec2,
        velocity: Vec2,
        radius: float,
        damage: Damage,
        knockback: float,
        ttl: float,
        sprite: pygame.Surface | None = None,
        spin: float = 0.0,
        trail_color: Color | None = None,
        acceleration: float = 0.0,
    ) -> Projectile:
        """Create and add a projectile to the physics world."""
        moment = pymunk.moment_for_circle(1.0, 0, radius)
        body = pymunk.Body(1.0, moment)
        body.position = position
        velocity_vec = Vec2d(*velocity)
        body.velocity = velocity_vec
        shape = pymunk.Circle(body, radius)
        shape.elasticity = 1.0
        shape.friction = 0.0
        shape.collision_type = PROJECTILE_COLLISION_TYPE
        world.space.add(body, shape)
        projectile = cls(
            world=world,
            owner=owner,
            body=body,
            shape=shape,
            damage=damage,
            knockback=knockback,
            ttl=ttl,
            max_ttl=ttl,
            sprite=sprite,
            spin=spin,
            trail_color=trail_color,
            acceleration=acceleration,
            last_velocity=Vec2d(velocity_vec.x, velocity_vec.y),
        )
        world.register_projectile(projectile)
        return projectile

    def step(self, dt: float) -> bool:
        """Advance state and return ``True`` while the projectile is alive."""
        self.ttl -= dt
        velocity = self.body.velocity
        if velocity.x * self.last_velocity.x < 0 or velocity.y * self.last_velocity.y < 0:
            self.bounces += 1
        self.last_velocity = Vec2d(velocity.x, velocity.y)
        if self.acceleration != 0.0:
            speed = sqrt(velocity.x * velocity.x + velocity.y * velocity.y)
            if speed > 0.0:
                new_speed = speed + self.acceleration * dt
                scale = new_speed / speed
                self.body.velocity = (velocity.x * scale, velocity.y * scale)
        if self.sprite is not None:
            if self.spin != 0.0:
                self.angle = (self.angle + self.spin * dt) % (2 * pi)
            else:
                velocity = self.body.velocity
                if velocity.x != 0.0 or velocity.y != 0.0:
                    self.angle = atan2(velocity.y, velocity.x) + pi / 2
        if self.trail_color is not None:
            pos = (float(self.body.position.x), float(self.body.position.y))
            self.trail.append(pos)
        return self.ttl > 0 or self.bounces < 2

    def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:
        pos = self.body.position
        dx = float(pos.x) - position[0]
        dy = float(pos.y) - position[1]
        rad = float(self.shape.radius) + radius
        return dx * dx + dy * dy <= rad * rad

    def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool:
        """Apply damage to ``target`` at ``timestamp`` and transfer momentum."""
        if target == self.owner:
            # Defensive check: ignore collisions against the projectile's owner.
            # Returning ``True`` keeps the projectile alive without side effects.
            return True

        owner_color = view.get_team_color(self.owner)
        target_color = view.get_team_color(target)
        mult = critical_multiplier(view, self.owner)
        amount = self.damage.amount * mult
        if owner_color == target_color:
            view.heal(target, amount, timestamp)
        else:
            view.deal_damage(target, Damage(amount), timestamp)
        if self.audio is not None:
            self.audio.on_touch(timestamp)
        target_pos = view.get_position(target)
        pos = self.body.position
        dx = pos.x - target_pos[0]
        dy = pos.y - target_pos[1]
        norm = sqrt(dx * dx + dy * dy) or 1.0
        view.apply_impulse(target, dx / norm * self.knockback, dy / norm * self.knockback)
        return False

    def retarget(self, target: Vec2, new_owner: EntityId) -> None:
        """Aim the projectile toward ``target`` and reset its lifetime."""
        px, py = float(self.body.position.x), float(self.body.position.y)
        dx, dy = target[0] - px, target[1] - py
        norm = sqrt(dx * dx + dy * dy) or 1.0
        vx, vy = float(self.body.velocity.x), float(self.body.velocity.y)
        speed = sqrt(vx * vx + vy * vy)
        self.body.velocity = (dx / norm * speed, dy / norm * speed)
        self.owner = new_owner
        self.ttl = self.max_ttl
        self.angle = atan2(dy, dx) + pi / 2
        self.bounces = 0
        self.last_velocity = Vec2d(self.body.velocity.x, self.body.velocity.y)

    def draw(self, renderer: Renderer, view: WorldView) -> None:
        pos = (float(self.body.position.x), float(self.body.position.y))
        if self.trail_color is not None and len(self.trail) > 1:
            denom = len(self.trail) - 1
            for i, (a, b) in enumerate(pairwise(self.trail)):
                t = (i + 1) / denom
                color = cast(Color, tuple(int(c * t) for c in self.trail_color))
                renderer.draw_line(a, b, color, self.trail_width)
        team_color: Color = view.get_team_color(self.owner)
        if self.sprite is not None:
            renderer.draw_sprite(
                self.sprite,
                pos,
                self.angle,
                aura_color=team_color,
                aura_radius=int(self.shape.radius),
            )
        else:
            renderer.draw_projectile(
                pos, int(self.shape.radius), (255, 255, 0), aura_color=team_color
            )
        if renderer.debug:
            renderer.draw_circle_outline(pos, float(self.shape.radius), (0, 255, 0))

    def destroy(self) -> None:
        self.destroyed = True
        self.world.unregister_projectile(self)
        self.world.space.remove(self.body, self.shape)
