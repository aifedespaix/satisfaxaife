from __future__ import annotations

import itertools
from dataclasses import dataclass

import pymunk

from app.core.types import Damage, EntityId, Stats, Vec2
from app.world.physics import PhysicsWorld

DEFAULT_BALL_RADIUS: float = 30.0
"""Default radius used for spawned balls in pixels."""

_id_gen = itertools.count(1)


@dataclass(slots=True)
class Ball:
    """Simple dynamic ball entity."""

    eid: EntityId
    body: pymunk.Body
    shape: pymunk.Circle
    stats: Stats
    health: float

    @classmethod
    def spawn(
        cls,
        world: PhysicsWorld,
        position: Vec2,
        radius: float = DEFAULT_BALL_RADIUS,
        stats: Stats | None = None,
    ) -> Ball:
        """Create and add a ball to the physics world."""
        eid = EntityId(next(_id_gen))
        moment = pymunk.moment_for_circle(1.0, 0, radius)
        body = pymunk.Body(1.0, moment)
        body.position = position
        shape = pymunk.Circle(body, radius)
        shape.elasticity = 1.0
        shape.friction = 0.0
        world.space.add(body, shape)
        stats = stats or Stats(max_health=100.0, max_speed=400.0)
        return cls(eid=eid, body=body, shape=shape, stats=stats, health=stats.max_health)

    def take_damage(self, damage: Damage) -> bool:
        """Apply damage and return True if entity is dead."""
        self.health -= damage.amount
        return self.health <= 0

    def cap_speed(self) -> None:
        """Limit the body's velocity to max speed."""
        vx, vy = self.body.velocity
        speed_sq = vx * vx + vy * vy
        max_speed = self.stats.max_speed
        if speed_sq > max_speed * max_speed:
            self.body.velocity = self.body.velocity.normalized() * max_speed
