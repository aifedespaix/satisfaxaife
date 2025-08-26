from __future__ import annotations

from app.world.entities import Ball
from app.world.physics import PhysicsWorld


def test_ball_spawn_default_radius() -> None:
    world = PhysicsWorld()
    ball = Ball.spawn(world, (0.0, 0.0))
    assert ball.shape.radius == 40.0
