import pygame

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


def test_substeps_high_speed_ball_wall_collision() -> None:
    """Balls moving at high speed still bounce on walls with substeps."""
    pygame.init()
    world = PhysicsWorld()
    ball = Ball.spawn(world, position=(50.0, 300.0), radius=20.0)
    ball.body.velocity = (-200000.0, 0.0)
    world.step(1 / 60, substeps=4)
    assert ball.body.position.x >= ball.shape.radius
