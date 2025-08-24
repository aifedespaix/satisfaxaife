from __future__ import annotations

from app.core.config import settings
from app.video.recorder import Recorder
from app.world.entities import Ball
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


def run_match(seconds: int, recorder: Recorder) -> None:
    """Run a minimal game loop and record frames."""
    world = PhysicsWorld()
    entities: list[Ball] = [Ball.spawn(world, (settings.width / 2, settings.height / 2))]
    projectiles: list[Projectile] = []

    total_frames = int(seconds * settings.fps)
    for frame in range(total_frames):
        for entity in entities:
            entity.cap_speed()
        for projectile in projectiles:
            projectile.step(settings.dt)
        world.step(settings.dt)
        recorder.add_frame(frame)

    recorder.close()
