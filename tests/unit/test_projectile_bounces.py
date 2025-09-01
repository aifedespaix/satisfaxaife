import pygame

from app.core.types import Damage, EntityId
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


def test_projectile_requires_two_bounces_for_expiration() -> None:
    pygame.init()
    world = PhysicsWorld()
    projectile = Projectile.spawn(
        world,
        owner=EntityId(1),
        position=(0.0, 0.0),
        velocity=(100.0, 0.0),
        radius=1.0,
        damage=Damage(1),
        knockback=0.0,
        ttl=0.1,
    )
    assert projectile.step(0.2) is True
    projectile.body.velocity = (-100.0, 0.0)
    assert projectile.step(0.0) is True
    assert projectile.bounces == 1
    projectile.body.velocity = (100.0, 0.0)
    assert projectile.step(0.0) is False
    assert projectile.bounces == 2


def test_retarget_resets_bounce_counter() -> None:
    pygame.init()
    world = PhysicsWorld()
    projectile = Projectile.spawn(
        world,
        owner=EntityId(1),
        position=(0.0, 0.0),
        velocity=(100.0, 0.0),
        radius=1.0,
        damage=Damage(1),
        knockback=0.0,
        ttl=1.0,
    )
    projectile.body.velocity = (-100.0, 0.0)
    projectile.step(0.0)
    assert projectile.bounces == 1
    projectile.retarget((0.0, 0.0), EntityId(2))
    assert projectile.bounces == 0
