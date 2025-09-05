"""Performance tests for the spatial index."""

from time import perf_counter
from typing import cast

from app.core.types import Damage, EntityId
from app.weapons.base import WorldView
from app.world.entities import Ball
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


class _NoopView:
    """Minimal view implementation for collision processing."""

    def get_position(self, eid: EntityId) -> tuple[float, float]:  # pragma: no cover - not used
        return (0.0, 0.0)

    def deal_damage(
        self, eid: EntityId, damage: Damage, timestamp: float
    ) -> None:  # pragma: no cover - not used
        pass

    def heal(self, eid: EntityId, amount: float, timestamp: float) -> None:  # pragma: no cover - not used
        pass

    def get_team_color(self, eid: EntityId) -> tuple[int, int, int]:  # pragma: no cover - simple
        return (0, 0, 0)

    def apply_impulse(
        self, eid: EntityId, vx: float, vy: float
    ) -> None:  # pragma: no cover - not used
        pass


def _build_world(count: int) -> PhysicsWorld:
    world = PhysicsWorld()
    spacing = 20.0
    for i in range(count):
        x = 50.0 + (i % 40) * spacing
        Ball.spawn(world, (x, 1920.0 - 50.0))
    for i in range(count):
        x = 50.0 + (i % 40) * spacing
        Projectile.spawn(
            world,
            owner=EntityId(0),
            position=(x, 50.0),
            velocity=(0.0, 0.0),
            radius=5.0,
            damage=Damage(0.0),
            knockback=0.0,
            ttl=1.0,
        )
    world.set_context(cast(WorldView, _NoopView()), 0.0)
    return world


def _run_once(world: PhysicsWorld) -> float:
    start = perf_counter()
    world._index.rebuild()  # noqa: SLF001 - internal benchmark
    world._process_projectile_collisions()  # noqa: SLF001 - internal benchmark
    return perf_counter() - start


def test_collision_scaling_is_quasi_linear() -> None:
    """Doubling entities should not quadruple processing time."""

    small = _build_world(200)
    large = _build_world(400)

    t_small = _run_once(small)
    t_large = _run_once(large)

    assert t_large <= t_small * 2.5
