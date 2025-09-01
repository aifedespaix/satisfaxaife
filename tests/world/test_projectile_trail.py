from collections import deque

import pygame

from app.core.types import Damage, EntityId, Vec2
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


class RecordingDeque(deque[Vec2]):
    """Deque that records ``pop`` and ``popleft`` calls."""

    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover - simple init
        super().__init__(*args, **kwargs)
        self.pop_calls = 0
        self.popleft_calls = 0

    def pop(self) -> Vec2:  # type: ignore[override]
        self.pop_calls += 1
        return super().pop()

    def popleft(self) -> Vec2:  # type: ignore[override]
        self.popleft_calls += 1
        return super().popleft()


def test_trail_is_bounded_without_manual_shifting() -> None:
    pygame.init()
    world = PhysicsWorld()
    projectile = Projectile.spawn(
        world,
        owner=EntityId(1),
        position=(0.0, 0.0),
        velocity=(0.0, 0.0),
        radius=1.0,
        damage=Damage(1),
        knockback=0.0,
        ttl=1.0,
        trail_color=(255, 255, 255),
    )
    recording_trail: RecordingDeque = RecordingDeque(maxlen=8)
    projectile.trail = recording_trail
    for i in range(10):
        projectile.body.position = (float(i), 0.0)
        projectile.step(0.0)
    assert len(projectile.trail) == 8
    assert list(projectile.trail)[0] == (2.0, 0.0)
    assert list(projectile.trail)[-1] == (9.0, 0.0)
    assert recording_trail.pop_calls == 0
    assert recording_trail.popleft_calls == 0

