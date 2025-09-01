from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pymunk

from app.core.config import settings

if TYPE_CHECKING:
    from app.weapons.base import WorldView

    from .entities import Ball
    from .projectiles import Projectile

import math
import pymunk

def _bb_intersect(a: pymunk.Shape, b: pymunk.Shape) -> bool:
    return a.bb.intersects(b.bb)

def _circles_overlap(a: pymunk.Shape, b: pymunk.Shape) -> bool:
    ca = isinstance(a, pymunk.Circle)
    cb = isinstance(b, pymunk.Circle)
    if not (ca and cb):
        return False
    pa = a.body.position
    pb = b.body.position
    ra = float(a.radius)
    rb = float(b.radius)
    dx = pa.x - pb.x
    dy = pa.y - pb.y
    return (dx*dx + dy*dy) <= (ra + rb)*(ra + rb)

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

    def register_projectile(self, projectile: Projectile) -> None:
        # On rend les projectiles "sensor" pour éviter tout push/ricochet physique.
        projectile.shape.sensor = True
        # projectile.shape.collision_type = 2  # optionnel si tu gardes des handlers ailleurs
        self._projectiles[projectile.shape] = projectile

    def unregister_projectile(self, projectile: Projectile) -> None:
        self._projectiles.pop(projectile.shape, None)

    def set_projectile_removed_callback(self, callback: Callable[[Projectile], None]) -> None:
        self._on_projectile_removed = callback

    def set_context(self, view: WorldView, timestamp: float) -> None:
        """Provide view and current timestamp for collision callbacks."""
        self._view = view
        self._timestamp = timestamp

    # ── Détection manuelle des collisions ─────────────────────────────────────

    def _process_collisions(self) -> None:
        """Détecte et traite les impacts projectile↔ball sans handlers Pymunk,
        en évitant le bug d'assert de ContactPointSet quand count==0."""
        if self._view is None:
            return

        for proj_shape, projectile in list(self._projectiles.items()):
            if getattr(projectile, "destroyed", False):
                continue

            for ball_shape, ball in self._balls.items():
<<<<<<< HEAD
                # 1) Rejet grossier par BB
                if not _bb_intersect(proj_shape, ball_shape):
                    continue
=======
                if ball.eid == projectile.owner:
                    # Un projectile ne peut pas toucher son propriétaire actuel.
                    continue
                # Test robuste de collision: renvoie un ContactPointSet
                cps = proj_shape.shapes_collide(ball_shape)
                # Impact s'il y a au moins un point de contact
                if cps.points:
                    keep = projectile.on_hit(self._view, ball.eid, self._timestamp)
>>>>>>> efb5b0d0ae4c33c9d62f2d707a7bd24b731d64dd

                hit = False

                # 2) Fast-path précis pour cercles (pas besoin de shapes_collide)
                if _circles_overlap(proj_shape, ball_shape):
                    hit = True
                else:
                    # 3) Cas génériques: appeler shapes_collide mais ignorer l'assertion 0-point
                    try:
                        cps = proj_shape.shapes_collide(ball_shape)
                        hit = bool(getattr(cps, "points", ()))  # ≥1 point => impact
                    except AssertionError:
                        # Bug Pymunk 7.1.0: count==0 → assert. On traite comme "pas d'impact".
                        hit = False

                if not hit:
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
            # Juste après la résolution physique, on détecte les hits côté gameplay.
            self._process_collisions()
