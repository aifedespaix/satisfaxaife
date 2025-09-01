import math

import pygame
import pytest

from app.core.types import Damage, EntityId
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


def test_projectile_reorients_and_trails() -> None:
    pygame.init()
    world = PhysicsWorld()
    sprite = pygame.Surface((10, 10))
    projectile = Projectile.spawn(
        world,
        owner=EntityId(1),
        position=(0.0, 0.0),
        velocity=(10.0, 0.0),
        radius=1.0,
        damage=Damage(1),
        knockback=0.0,
        ttl=1.0,
        sprite=sprite,
        trail_color=(255, 255, 255),
    )
    projectile.step(0.1)
    assert projectile.angle == pytest.approx(math.pi / 2)
    assert len(projectile.trail) == 1
    projectile.body.velocity = (0.0, 10.0)
    projectile.step(0.1)
    assert projectile.angle == pytest.approx(math.pi)
    assert len(projectile.trail) == 2


def test_projectile_accelerates() -> None:
    pygame.init()
    world = PhysicsWorld()
    projectile = Projectile.spawn(
        world,
        owner=EntityId(1),
        position=(0.0, 0.0),
        velocity=(10.0, 0.0),
        radius=1.0,
        damage=Damage(1),
        knockback=0.0,
        ttl=1.0,
        acceleration=10.0,
    )
    projectile.step(0.5)
    vx = float(projectile.body.velocity.x)
    speed = math.hypot(vx, float(projectile.body.velocity.y))
    assert speed == pytest.approx(15.0)
