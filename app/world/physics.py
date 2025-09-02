"""Physics world wrapper with manual collision detection."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pymunk
from app.core.config import settings

from .spatial_index import SpatialIndex

if TYPE_CHECKING:
    from app.weapons.base import WorldView

    from .entities import Ball
    from .projectiles import Projectile


def _bb_intersect(a: pymunk.Shape, b: pymunk.Shape) -> bool:
    return bool(a.bb.intersects(b.bb))


def _circles_overlap(a: pymunk.Shape, b: pymunk.Shape) -> bool:
    if not isinstance(a, pymunk.Circle) or not isinstance(b, pymunk.Circle):
        return False
    pa = a.body.position
    pb = b.body.position
    ra = float(a.radius)
    rb = float(b.radius)
    dx = pa.x - pb.x
    dy = pa.y - pb.y
    return bool((dx * dx + dy * dy) <= (ra + rb) * (ra + rb))


def _shapes_hit(proj_shape: pymunk.Shape, ball_shape: pymunk.Shape) -> bool:
    """Return ``True`` when the two shapes overlap."""

    if not _bb_intersect(proj_shape, ball_shape):
        return False
    if _circles_overlap(proj_shape, ball_shape):
        return True
    try:
        cps = proj_shape.shapes_collide(ball_shape)
        return bool(getattr(cps, "points", ()))
    except AssertionError:
        # Bug Pymunk 7.1.0: count==0 → assert. Treated as "no impact".
        return False


def _resolve_ball_collision(ball_a: Ball, ball_b: Ball) -> None:
    """Resolve an overlap between two balls with a perfect elastic bounce."""

    pa = ball_a.body.position
    pb = ball_b.body.position
    dx = pb.x - pa.x
    dy = pb.y - pa.y
    dist_sq = dx * dx + dy * dy
    if dist_sq == 0.0:
        return
    dist = dist_sq**0.5

    ra = float(ball_a.shape.radius)
    rb = float(ball_b.shape.radius)
    overlap = (ra + rb) - dist
    if overlap <= 0:
        return

    nx = dx / dist
    ny = dy / dist
    shift = overlap / 2.0
    ball_a.body.position = (pa.x - nx * shift, pa.y - ny * shift)
    ball_b.body.position = (pb.x + nx * shift, pb.y + ny * shift)

    vax, vay = ball_a.body.velocity
    vbx, vby = ball_b.body.velocity
    va_n = vax * nx + vay * ny
    vb_n = vbx * nx + vby * ny
    va_t_x = vax - nx * va_n
    va_t_y = vay - ny * va_n
    vb_t_x = vbx - nx * vb_n
    vb_t_y = vby - ny * vb_n
    ball_a.body.velocity = (va_t_x + nx * vb_n, va_t_y + ny * vb_n)
    ball_b.body.velocity = (vb_t_x + nx * va_n, vb_t_y + ny * va_n)


class PhysicsWorld:
    """Encapsulates the pymunk space and static boundaries."""

    def __init__(self) -> None:
        self.space = pymunk.Space()
        self.space.gravity = (0.0, 0.0)
        self._projectiles: dict[pymunk.Shape, Projectile] = {}
        self._balls: dict[pymunk.Shape, Ball] = {}
        self._index = SpatialIndex()
        self._on_projectile_removed: Callable[[Projectile], None] | None = None
        self._view: WorldView | None = None
        self._timestamp: float = 0.0
        self._add_bounds()

        # NOTE: certains environnements Pymunk n'exposent pas les handlers.
        # On passe en détection manuelle robuste (voir _process_collisions()).
        # self._register_handlers()  # ← on n’en a plus besoin

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

    # ── Enregistrement entités ────────────────────────────────────────────────

    def register_ball(self, ball: Ball) -> None:
        # Optionnel: tu peux poser un collision_type si tu le réutilises ailleurs
        # ball.shape.collision_type = 1
        self._balls[ball.shape] = ball
        self._index.track(ball.shape)

    def register_projectile(self, projectile: Projectile) -> None:
        # On rend les projectiles "sensor" pour éviter tout push/ricochet physique.
        projectile.shape.sensor = True
        # projectile.shape.collision_type = 2  # optionnel si tu gardes des handlers ailleurs
        self._projectiles[projectile.shape] = projectile
        self._index.track(projectile.shape)

    def unregister_projectile(self, projectile: Projectile) -> None:
        self._projectiles.pop(projectile.shape, None)
        self._index.untrack(projectile.shape)

    def set_projectile_removed_callback(self, callback: Callable[[Projectile], None]) -> None:
        self._on_projectile_removed = callback

    def set_context(self, view: WorldView, timestamp: float) -> None:
        """Provide view and current timestamp for collision callbacks."""
        self._view = view
        self._timestamp = timestamp

    # ── Détection manuelle des collisions ─────────────────────────────────────

    def _process_ball_collisions(self) -> None:
        """Resolve ball↔ball overlaps that escaped the physics solver."""

        processed: set[pymunk.Shape] = set()
        for shape, ball in self._balls.items():
            for candidate in self._index.query(shape):
                if candidate is shape or candidate in processed:
                    continue
                other = self._balls.get(candidate)
                if other is None or not _shapes_hit(shape, candidate):
                    continue
                _resolve_ball_collision(ball, other)
            processed.add(shape)

    def _process_projectile_collisions(self) -> None:
        """Détecte et traite les impacts projectile↔ball sans handlers Pymunk,
        en évitant le bug d'assert de ContactPointSet quand count==0."""
        if self._view is None:
            return

        for proj_shape, projectile in list(self._projectiles.items()):
            if getattr(projectile, "destroyed", False):
                continue

            for candidate in self._index.query(proj_shape):
                ball = self._balls.get(candidate)
                if ball is None or not _shapes_hit(proj_shape, candidate):
                    continue

                if ball.eid == projectile.owner:
                    # Skip self-collisions so a deflected projectile cannot
                    # immediately hit its new owner.
                    continue

                keep = projectile.on_hit(self._view, ball.eid, self._timestamp)
                if not keep:
                    projectile.destroy()
                    cb = self._on_projectile_removed
                    if cb is not None:
                        cb(projectile)
                    break  # projectile supprimé → passe au suivant

    # ── Simulation ────────────────────────────────────────────────────────────

    def step(self, dt: float, substeps: int = 1) -> None:
        """Advance the physics simulation."""
        if substeps < 1:
            raise ValueError("substeps must be >= 1")

        sub_dt = dt / float(substeps)
        for _ in range(substeps):
            self.space.step(sub_dt)
            self._index.rebuild()
            # Collision resolution après la simulation physique.
            self._process_ball_collisions()
            self._process_projectile_collisions()
