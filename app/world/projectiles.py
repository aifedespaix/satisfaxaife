from __future__ import annotations

from dataclasses import dataclass

import pymunk

from app.core.types import Damage, EntityId, Vec2
from app.world.physics import PhysicsWorld


@dataclass(slots=True)
class Projectile:
    """Dynamic projectile with a limited lifetime."""

    owner: EntityId
    body: pymunk.Body
    shape: pymunk.Circle
    damage: Damage
    knockback: float
    ttl: float

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
        return cls(owner=owner, body=body, shape=shape, damage=damage, knockback=knockback, ttl=ttl)

    def step(self, dt: float) -> bool:
        """Advance state and return True if still alive."""
        self.ttl -= dt
        return self.ttl > 0
