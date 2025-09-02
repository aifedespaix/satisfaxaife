import pygame

from app.world.entities import Ball
from app.world.physics import PhysicsWorld


def test_high_speed_balls_collide() -> None:
    pygame.init()
    world = PhysicsWorld()
    left = Ball.spawn(world, position=(100.0, 300.0), radius=20.0)
    right = Ball.spawn(world, position=(700.0, 300.0), radius=20.0)
    left.body.velocity = (200000.0, 0.0)
    right.body.velocity = (-200000.0, 0.0)
    world.step(1 / 60)
    assert left.body.position.x < right.body.position.x
    assert left.body.velocity.x < 0
    assert right.body.velocity.x > 0
