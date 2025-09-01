from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pymunk

from app.core.config import settings

# ``pymunk.version_info`` already exposes numeric components. Using it avoids
# string parsing and ensures version comparisons operate on integers.
PYMUNK_VERSION = tuple(pymunk.version_info[:2])
PYMUNK_VERSION_STR = ".".join(map(str, pymunk.version_info))

if TYPE_CHECKING:
    from app.weapons.base import WorldView

    from .entities import Ball
    from .projectiles import Projectile


class PhysicsWorld:
    """Encapsulates the pymunk space and static boundaries."""

    def __init__(self) -> None:
        self.space = pymunk.Space()
        self.space.gravity = (0.0, 0.0)
        self._projectiles: dict[pymunk.Shape, Projectile] = {}
        self._balls: dict[pymunk.Shape, Ball] = {}
        self._on_projectile_removed: Callable[[Projectile], None] | None = None
        self._view: WorldView | None = None
        self._timestamp: float = 0.0
        self._add_bounds()
        if PYMUNK_VERSION < (7, 0):
            msg = (
                "PhysicsWorld requires pymunk >= 7.0, found "
                f"{PYMUNK_VERSION_STR}. Please upgrade pymunk."
            )
            raise RuntimeError(msg)
        self._register_handlers()

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

    def _register_handlers(self) -> None:
        """Register collision callbacks for projectiles hitting balls."""

        from .entities import BALL_COLLISION_TYPE
        from .projectiles import PROJECTILE_COLLISION_TYPE

        if hasattr(self.space, "add_collision_handler"):
            handler = self.space.add_collision_handler(
                PROJECTILE_COLLISION_TYPE, BALL_COLLISION_TYPE
            )
        else:
            handler = self.space.collision_handler(PROJECTILE_COLLISION_TYPE, BALL_COLLISION_TYPE)
        handler.begin = self._handle_projectile_hit

    def register_ball(self, ball: Ball) -> None:
        self._balls[ball.shape] = ball

    def register_projectile(self, projectile: Projectile) -> None:
        self._projectiles[projectile.shape] = projectile

    def unregister_projectile(self, projectile: Projectile) -> None:
        self._projectiles.pop(projectile.shape, None)

    def set_projectile_removed_callback(self, callback: Callable[[Projectile], None]) -> None:
        self._on_projectile_removed = callback

    def set_context(self, view: WorldView, timestamp: float) -> None:
        """Provide view and current timestamp for collision callbacks."""
        self._view = view
        self._timestamp = timestamp

    def _handle_projectile_hit(
        self, arbiter: pymunk.Arbiter, _space: pymunk.Space, _data: object
    ) -> bool:
        proj_shape, ball_shape = arbiter.shapes
        projectile = self._projectiles.get(proj_shape)
        ball = self._balls.get(ball_shape)
        if projectile is None or ball is None or self._view is None:
            return True
        keep = projectile.on_hit(self._view, ball.eid, self._timestamp)
        if not keep:
            projectile.destroy()
            if self._on_projectile_removed is not None:
                self._on_projectile_removed(projectile)
        return False

    def step(self, dt: float, substeps: int = 1) -> None:
        """Advance the physics simulation.

        Parameters
        ----------
        dt:
            Total delta time for this update in seconds.
        substeps:
            Number of internal substeps used to integrate ``dt``. A value of
            one performs a single step, while higher values subdivide ``dt`` to
            reduce tunneling when entities move at high speed. Must be at least
            one.

        Raises
        ------
        ValueError
            If ``substeps`` is less than one.
        """

        if substeps < 1:
            msg = "substeps must be >= 1"
            raise ValueError(msg)

        sub_dt = dt / float(substeps)
        for _ in range(substeps):
            self.space.step(sub_dt)
