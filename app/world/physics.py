from __future__ import annotations

import pymunk

from app.core.config import settings


class PhysicsWorld:
    """Encapsulates the pymunk space and static boundaries."""

    def __init__(self) -> None:
        self.space = pymunk.Space()
        self.space.gravity = (0.0, 0.0)
        self._add_bounds()

    def _add_bounds(self) -> None:
        thickness = float(settings.wall_thickness)
        w, h = settings.width, settings.height
        static = self.space.static_body
        segments = [
            pymunk.Segment(static, (0, 0), (w, 0), thickness),
            pymunk.Segment(static, (0, 0), (0, h), thickness),
            pymunk.Segment(static, (w, 0), (w, h), thickness),
            pymunk.Segment(static, (0, h), (w, h), thickness),
        ]
        for segment in segments:
            segment.elasticity = 1.0
            segment.friction = 0.0
        self.space.add(*segments)

    def step(self, dt: float) -> None:
        self.space.step(dt)
