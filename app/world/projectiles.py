from __future__ import annotations

from dataclasses import dataclass, field
from math import atan2, pi, sqrt
from typing import cast

import pygame
import pymunk

from app.audio.weapons import WeaponAudio
from app.core.types import Color, Damage, EntityId, Vec2
from app.render.renderer import Renderer
from app.weapons.base import WeaponEffect, WorldView
from app.world.physics import PhysicsWorld

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
    trail: list[Vec2] = field(default_factory=list)
    trail_width: int = 2
    acceleration: float = 0.0
    bounces: int = 0
    last_velocity: Vec2 = (0.0, 0.0)

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
        body.velocity = velocity
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
            last_velocity=(float(velocity[0]), float(velocity[1])),
        )
        world.register_projectile(projectile)
        return projectile

    def step(self, dt: float) -> bool:
        """Advance state and return ``True`` while the projectile is alive."""
        self.ttl -= dt
        vx = float(self.body.velocity.x)
        vy = float(self.body.velocity.y)
        if vx * self.last_velocity[0] < 0 or vy * self.last_velocity[1] < 0:
            self.bounces += 1
        self.last_velocity = (vx, vy)
        if self.acceleration != 0.0:
            speed = sqrt(vx * vx + vy * vy)
            if speed > 0.0:
                new_speed = speed + self.acceleration * dt
                scale = new_speed / speed
                self.body.velocity = (vx * scale, vy * scale)
        if self.sprite is not None:
            if self.spin != 0.0:
                self.angle = (self.angle + self.spin * dt) % (2 * pi)
            else:
                vx = float(self.body.velocity.x)
                vy = float(self.body.velocity.y)
                if vx != 0.0 or vy != 0.0:
                    self.angle = atan2(vy, vx) + pi / 2
        if self.trail_color is not None:
            pos = (float(self.body.position.x), float(self.body.position.y))
            self.trail.append(pos)
            if len(self.trail) > 8:
                self.trail.pop(0)
        return self.ttl > 0 or self.bounces < 2

    def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:
        pos = self.body.position
        dx = float(pos.x) - position[0]
        dy = float(pos.y) - position[1]
        rad = cast(float, self.shape.radius) + radius
        return dx * dx + dy * dy <= rad * rad

    def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool:
        """Apply damage to ``target`` at ``timestamp`` and transfer momentum."""
        view.deal_damage(target, self.damage, timestamp)
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
        self.last_velocity = (
            float(self.body.velocity.x),
            float(self.body.velocity.y),
        )

    def draw(self, renderer: Renderer, view: WorldView) -> None:
        pos = (float(self.body.position.x), float(self.body.position.y))
        if self.trail_color is not None and len(self.trail) > 1:
            denom = len(self.trail) - 1
            for i, (a, b) in enumerate(zip(self.trail, self.trail[1:], strict=False)):
                t = (i + 1) / denom
                color = cast(Color, tuple(int(c * t) for c in self.trail_color))
                renderer.draw_line(a, b, color, self.trail_width)
        if self.sprite is not None:
            renderer.draw_sprite(self.sprite, pos, self.angle)
        else:
            renderer.draw_projectile(pos, int(self.shape.radius), (255, 255, 0))

    def destroy(self) -> None:
        self.world.unregister_projectile(self)
        self.world.space.remove(self.body, self.shape)
