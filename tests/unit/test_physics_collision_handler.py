import pytest

pymunk = pytest.importorskip("pymunk")
pygame = pytest.importorskip("pygame")

from app.core.types import Damage, EntityId  # noqa: E402
from app.world.entities import Ball  # noqa: E402
from app.world.physics import PhysicsWorld  # noqa: E402
from app.world.projectiles import Projectile  # noqa: E402
from tests.helpers import StubWorldView  # noqa: E402


class _TrackingPhysicsWorld(PhysicsWorld):
    """Physics world subclass tracking projectile hit callbacks."""

    def __init__(self) -> None:
        super().__init__()
        self.hit_called = False

    def _handle_projectile_hit(
        self, arbiter: object, space: object, data: object
    ) -> bool:
        self.hit_called = True
        return super()._handle_projectile_hit(arbiter, space, data)


def test_projectile_collision_triggers_handler() -> None:
    """Collisions invoke the projectile hit handler without errors."""
    pygame.init()
    world = _TrackingPhysicsWorld()
    ball = Ball.spawn(world, position=(400.0, 300.0), radius=20.0)
    view = StubWorldView(ball)
    world.set_context(view, 0.0)

    Projectile.spawn(
        world,
        owner=EntityId(1),
        position=(400.0, 300.0),
        velocity=(0.0, 0.0),
        radius=5.0,
        damage=Damage(1.0),
        knockback=0.0,
        ttl=1.0,
    )

    world.step(1 / 60)
    assert world.hit_called
