from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import cast

import pygame
import pymunk

from app.core.types import Damage, EntityId, Vec2
from app.render.renderer import Renderer
from app.weapons.base import WeaponEffect, WorldView
from app.world.physics import PhysicsWorld


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
    sprite: pygame.Surface | None = None
    angle: float = 0.0
    spin: float = 0.0

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
    ) -> Projectile:
        """Create and add a projectile to the physics world."""
        moment = pymunk.moment_for_circle(1.0, 0, radius)
        body = pymunk.Body(1.0, moment)
        body.position = position
        body.velocity = velocity
        shape = pymunk.Circle(body, radius)
        shape.elasticity = 1.0
        shape.friction = 0.0
        world.space.add(body, shape)
        return cls(
            world=world,
            owner=owner,
            body=body,
            shape=shape,
            damage=damage,
            knockback=knockback,
            ttl=ttl,
            sprite=sprite,
            spin=spin,
        )

    def step(self, dt: float) -> bool:
        """Advance state and return ``True`` while the projectile is alive."""
        self.ttl -= dt
        if self.sprite is not None and self.spin != 0.0:
            self.angle = (self.angle + self.spin * dt) % (2 * 3.14159)
        return self.ttl > 0

    def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:
        pos = self.body.position
        dx = float(pos.x) - position[0]
        dy = float(pos.y) - position[1]
        rad = cast(float, self.shape.radius) + radius
        return dx * dx + dy * dy <= rad * rad

    def on_hit(self, view: WorldView, target: EntityId) -> bool:
        view.deal_damage(target, self.damage)
        target_pos = view.get_position(target)
        pos = self.body.position
        dx = pos.x - target_pos[0]
        dy = pos.y - target_pos[1]
        norm = sqrt(dx * dx + dy * dy) or 1.0
        view.apply_impulse(target, dx / norm * self.knockback, dy / norm * self.knockback)
        return False

    def draw(self, renderer: Renderer, view: WorldView) -> None:
        pos = (float(self.body.position.x), float(self.body.position.y))
        if self.sprite is not None:
            renderer.draw_sprite(self.sprite, pos, self.angle)
        else:
            renderer.draw_projectile(pos, int(self.shape.radius), (255, 255, 0))

    def destroy(self) -> None:
        self.world.space.remove(self.body, self.shape)
