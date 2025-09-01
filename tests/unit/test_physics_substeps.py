import pygame
import pytest

from app.core.config import settings
from app.core.types import Damage, EntityId
from app.world.entities import Ball
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile
from tests.helpers import StubWorldView


def test_substeps_high_speed_projectile_collision() -> None:
    """High-speed projectiles still collide when using substeps."""
    pygame.init()
    world = PhysicsWorld()
    ball = Ball.spawn(world, position=(400.0, 300.0), radius=20.0)
    view = StubWorldView(ball)
    world.set_context(view, 0.0)
    Projectile.spawn(
        world,
        owner=EntityId(1),
        position=(100.0, 300.0),
        velocity=(200000.0, 0.0),
        radius=5.0,
        damage=Damage(10.0),
        knockback=0.0,
        ttl=1.0,
    )
    world.step(1 / 60, substeps=4)
    assert ball.health < ball.stats.max_health


@pytest.mark.parametrize(
    ("position", "velocity", "axis", "limit", "sign"),
    [
        ((50.0, settings.height * 0.5), (-200000.0, 0.0), "x", 20.0, 1),
        (
            (settings.width - 50.0, settings.height * 0.5),
            (200000.0, 0.0),
            "x",
            settings.width - 20.0,
            -1,
        ),
        ((settings.width * 0.5, 50.0), (0.0, -200000.0), "y", 20.0, 1),
        (
            (settings.width * 0.5, settings.height - 50.0),
            (0.0, 200000.0),
            "y",
            settings.height - 20.0,
            -1,
        ),
    ],
)
def test_substeps_high_speed_ball_wall_collision_all_sides(
    position: tuple[float, float],
    velocity: tuple[float, float],
    axis: str,
    limit: float,
    sign: int,
) -> None:
    """Balls moving at high speed bounce off every wall with substeps."""
    pygame.init()
    world = PhysicsWorld()
    ball = Ball.spawn(world, position=position, radius=20.0)
    ball.body.velocity = velocity
    world.step(1 / 60, substeps=4)

    pos_val = getattr(ball.body.position, axis)
    vel_val = getattr(ball.body.velocity, axis)
    if sign > 0:
        assert pos_val >= limit
        assert vel_val > 0
    else:
        assert pos_val <= limit
        assert vel_val < 0
