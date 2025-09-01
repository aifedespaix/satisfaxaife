from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pymunk

from app.core.config import settings

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
        """Détecte et traite les impacts projectile↔ball sans utiliser les handlers Pymunk."""
        if self._view is None:
            return

        # On itère sur une copie pour tolérer la suppression de projectiles pendant la boucle.
        for proj_shape, projectile in list(self._projectiles.items()):
            # Skip si déjà détruit côté gameplay
            if getattr(projectile, "destroyed", False):
                continue

            for ball_shape, ball in self._balls.items():
                if ball.eid == projectile.owner:
                    # Un projectile ne peut pas toucher son propriétaire actuel.
                    continue
                # Test robuste de collision: renvoie un ContactPointSet
                cps = proj_shape.shapes_collide(ball_shape)
                # Impact s'il y a au moins un point de contact
                if cps.points:
                    keep = projectile.on_hit(self._view, ball.eid, self._timestamp)

                    if not keep:
                        # Détruit et notifie
                        projectile.destroy()
                        if self._on_projectile_removed is not None:
                            self._on_projectile_removed(projectile)
                        # On arrête d’examiner ce projectile (il n’existe plus)
                        break

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
