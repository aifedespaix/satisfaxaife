from __future__ import annotations

from dataclasses import dataclass

import pymunk

from app.core.types import Damage, Vec2
from app.world.physics import PhysicsWorld


@dataclass(slots=True)
class Projectile:
    """Simple projectile that moves and deals damage on hit."""

    body: pymunk.Body
    shape: pymunk.Circle
    damage: Damage

    @classmethod
    def spawn(
        cls,
        world: PhysicsWorld,
        position: Vec2,
        velocity: Vec2,
        radius: float = 5.0,
        damage: Damage | None = None,
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
        damage = damage or Damage(amount=10.0)
        return cls(body=body, shape=shape, damage=damage)

    def step(self, dt: float) -> None:  # noqa: ARG002 - future use
        """Advance the projectile state for one frame."""
        # Physics is handled by the world; placeholder for extra logic.
        return
