"""Physics world wrapper with manual collision detection."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pymunk
from app.core.config import settings
from app.core.targeting import _lead_target
from app.core.types import EntityId
from pymunk import Vec2 as Vec2d

from .spatial_index import SpatialIndex

if TYPE_CHECKING:
    from app.weapons.base import WorldView

    from .entities import Ball
    from .projectiles import Projectile


PROJECTILE_COLLISION_COOLDOWN: float = 1.0
"""Seconds before the same projectile pair can collide again."""


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
        self._proj_collision_cooldowns: dict[tuple[pymunk.Shape, pymunk.Shape], float] = {}
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
        to_remove = [key for key in self._proj_collision_cooldowns if projectile.shape in key]
        for key in to_remove:
            self._proj_collision_cooldowns.pop(key, None)

    def set_projectile_removed_callback(self, callback: Callable[[Projectile], None]) -> None:
        self._on_projectile_removed = callback

    def set_context(self, view: WorldView, timestamp: float) -> None:
        """Provide view and current timestamp for collision callbacks."""
        self._view = view
        self._timestamp = timestamp

    def _cleanup_projectile_cooldowns(self) -> None:
        """Remove outdated projectile collision cooldown entries."""
        threshold = self._timestamp - PROJECTILE_COLLISION_COOLDOWN
        for key, ts in list(self._proj_collision_cooldowns.items()):
            if ts < threshold or any(shape not in self._projectiles for shape in key):
                self._proj_collision_cooldowns.pop(key, None)

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

    def _retarget_after_swap(
        self, projectile: Projectile, new_owner: EntityId, view: WorldView
    ) -> None:
        """Assign ``new_owner`` and aim the projectile at their enemy.

        The projectile is redirected using an anticipatory targeting function
        that accounts for the enemy's current velocity. If the owner has no
        enemy, the projectile simply reverses direction.
        """

        enemy = view.get_enemy(new_owner)
        if enemy is not None:
            shooter_pos = (float(projectile.body.position.x), float(projectile.body.position.y))
            enemy_pos = view.get_position(enemy)
            enemy_vel = view.get_velocity(enemy)
            vx, vy = projectile.body.velocity
            speed = float((vx * vx + vy * vy) ** 0.5)
            dir_x, dir_y = _lead_target(shooter_pos, enemy_pos, enemy_vel, speed)
            target = (shooter_pos[0] + dir_x, shooter_pos[1] + dir_y)
            projectile.retarget(target, new_owner)
        else:
            vx, vy = projectile.body.velocity
            projectile.body.velocity = (-vx, -vy)
            projectile.owner = new_owner
            projectile.ttl = projectile.max_ttl
            projectile.last_velocity = Vec2d(projectile.body.velocity.x, projectile.body.velocity.y)

    def _handle_projectile_projectile(
        self,
        projectile: Projectile,
        proj_shape: pymunk.Shape,
        candidate: pymunk.Shape,
        processed: set[pymunk.Shape],
        view: WorldView,
    ) -> bool:
        """Return ``True`` if a projectile↔projectile collision was handled."""
        other_proj = self._projectiles.get(candidate)
        if (
            other_proj is None
            or candidate in processed
            or candidate is proj_shape
            or getattr(other_proj, "destroyed", False)
            or not _shapes_hit(proj_shape, candidate)
        ):
            return False

        key = (proj_shape, candidate) if id(proj_shape) < id(candidate) else (candidate, proj_shape)
        last = self._proj_collision_cooldowns.get(key)
        if last is not None and self._timestamp - last < PROJECTILE_COLLISION_COOLDOWN:
            return False

        self._proj_collision_cooldowns[key] = self._timestamp

        owner_a, owner_b = projectile.owner, other_proj.owner
        self._retarget_after_swap(projectile, owner_b, view)
        self._retarget_after_swap(other_proj, owner_a, view)
        if projectile.audio is not None:
            projectile.audio.on_touch(self._timestamp)
        if other_proj.audio is not None:
            other_proj.audio.on_touch(self._timestamp)
        processed.add(proj_shape)
        processed.add(candidate)
        return True

    def _handle_projectile_ball(
        self,
        projectile: Projectile,
        proj_shape: pymunk.Shape,
        candidate: pymunk.Shape,
        view: WorldView,
    ) -> bool:
        """Return ``True`` if a projectile hit a ball and was removed."""
        ball = self._balls.get(candidate)
        if ball is None or not _shapes_hit(proj_shape, candidate):
            return False
        if ball.eid == projectile.owner:
            # Skip self-collisions so a deflected projectile cannot immediately
            # hit its new owner.
            return False
        keep = projectile.on_hit(view, ball.eid, self._timestamp)
        if not keep:
            projectile.destroy()
            cb = self._on_projectile_removed
            if cb is not None:
                cb(projectile)
            return True
        return False

    def _process_projectile_collisions(self) -> None:
        """Process projectile↔ball and projectile↔projectile overlaps."""
        view = self._view
        if view is None:
            return

        self._cleanup_projectile_cooldowns()

        processed: set[pymunk.Shape] = set()

        for proj_shape, projectile in list(self._projectiles.items()):
            if getattr(projectile, "destroyed", False):
                continue

            for candidate in self._index.query(proj_shape):
                if self._handle_projectile_projectile(
                    projectile, proj_shape, candidate, processed, view
                ):
                    break
                if self._handle_projectile_ball(projectile, proj_shape, candidate, view):
                    break

            processed.add(proj_shape)

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
