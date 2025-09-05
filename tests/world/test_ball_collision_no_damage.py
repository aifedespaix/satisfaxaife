from __future__ import annotations

import pytest

from app.world.entities import Ball
from app.world.physics import PhysicsWorld, _resolve_ball_collision


def test_resolve_ball_collision_applies_physics_without_damage() -> None:
    world = PhysicsWorld()
    ball_a = Ball.spawn(world, (0.0, 0.0))
    ball_b = Ball.spawn(world, (70.0, 0.0))
    ball_a.body.velocity = (10.0, 0.0)
    ball_b.body.velocity = (-10.0, 0.0)

    _resolve_ball_collision(ball_a, ball_b)

    assert ball_a.health == ball_a.stats.max_health
    assert ball_b.health == ball_b.stats.max_health
    assert abs(ball_a.body.velocity.x + 10.0) < 1e-6
    assert abs(ball_b.body.velocity.x - 10.0) < 1e-6
