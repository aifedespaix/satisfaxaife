"""Target prediction utilities for projectile aiming.

This module centralises ballistic helper functions used across the AI and
physics layers. Extracting them from :mod:`app.ai.policy` reduces coupling
between unrelated systems and enables reuse without importing heavy AI
modules.
"""

from __future__ import annotations

import math

from app.core.types import Vec2

__all__ = ["_lead_target"]


def _lead_target(
    shooter: Vec2,
    target_pos: Vec2,
    target_vel: Vec2,
    projectile_speed: float,
) -> Vec2:
    """Return a unit vector leading the *target* given its velocity.

    The function solves a quadratic equation to predict the interception
    point of a projectile travelling at ``projectile_speed`` toward a target
    moving linearly at ``target_vel``. If no valid interception time exists,
    the current direction to the target is returned.
    """

    tx = target_pos[0] - shooter[0]
    ty = target_pos[1] - shooter[1]
    vx, vy = target_vel
    if projectile_speed <= 0.0:
        norm = math.hypot(tx, ty) or 1.0
        return (tx / norm, ty / norm)

    a = vx * vx + vy * vy - projectile_speed * projectile_speed
    b = 2.0 * (tx * vx + ty * vy)
    c = tx * tx + ty * ty

    if abs(a) < 1e-6:
        t = -c / b if abs(b) > 1e-6 else 0.0
    else:
        disc = b * b - 4.0 * a * c
        if disc < 0.0:
            t = 0.0
        else:
            sqrt_disc = math.sqrt(disc)
            t1 = (-b - sqrt_disc) / (2.0 * a)
            t2 = (-b + sqrt_disc) / (2.0 * a)
            candidates = [t for t in (t1, t2) if t > 0.0]
            t = min(candidates, default=0.0)

    ex = target_pos[0] + vx * t
    ey = target_pos[1] + vy * t
    dir_x = ex - shooter[0]
    dir_y = ey - shooter[1]
    norm = math.hypot(dir_x, dir_y) or 1.0
    return (dir_x / norm, dir_y / norm)

