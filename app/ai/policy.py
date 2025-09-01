from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from app.core.types import EntityId, Vec2
from app.weapons.base import WorldView


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


@dataclass(slots=True)
class SimplePolicy:
    """Very small deterministic combat policy."""

    style: Literal["aggressive", "kiter"]
    vertical_offset: float = 0.1
    dodge_bias: float = 0.5
    desired_dist_factor: float = 0.5
    fire_range_factor: float = 0.8

    def decide(
        self, me: EntityId, view: WorldView, projectile_speed: float | None = None
    ) -> tuple[Vec2, Vec2, bool]:
        """Return acceleration, facing vector and fire decision.

        When health drops below ``15%`` the policy retreats from the enemy but
        still evaluates firing as usual.
        """
        enemy = view.get_enemy(me)
        assert enemy is not None
        my_pos = view.get_position(me)
        enemy_pos = view.get_position(enemy)
        enemy_vel = view.get_velocity(enemy)
        dx = enemy_pos[0] - my_pos[0]
        dy = enemy_pos[1] - my_pos[1]
        dist = math.hypot(dx, dy)
        direction = (dx / dist, dy / dist) if dist else (1.0, 0.0)
        my_health = view.get_health_ratio(me)

        face: Vec2 = _lead_target(my_pos, enemy_pos, enemy_vel, projectile_speed or 0.0)
        cos_thresh = math.cos(math.radians(18))

        fleeing = my_health < 0.15

        if self.style == "aggressive":
            accel, fire = self._aggressive(me, view, my_pos, direction, dist, face, cos_thresh)
        else:
            accel, fire = self._kiter(direction, dist, face, cos_thresh, projectile_speed)

        if fleeing:
            accel = (-direction[0] * 400.0, -direction[1] * 400.0)

        if abs(dy) <= 1e-6:
            offset_face = (direction[0], self.vertical_offset)
            norm = math.hypot(*offset_face) or 1.0
            face = (offset_face[0] / norm, offset_face[1] / norm)

        return accel, face, fire

    def _aggressive(
        self,
        me: EntityId,
        view: WorldView,
        my_pos: Vec2,
        direction: Vec2,
        dist: float,
        face: Vec2,
        cos_thresh: float,
    ) -> tuple[Vec2, bool]:
        """Close combat behaviour prioritising projectile dodging."""

        dodge = (0.0, 0.0)
        closest_t = float("inf")
        best_vel: Vec2 | None = None
        for proj in view.iter_projectiles(excluding=me):
            px, py = proj.position
            vx, vy = proj.velocity
            rx = px - my_pos[0]
            ry = py - my_pos[1]
            approach = rx * vx + ry * vy
            if approach >= 0.0:
                continue
            speed_sq = vx * vx + vy * vy
            if speed_sq <= 1e-6:
                continue
            t = -approach / speed_sq
            if t >= closest_t or t > 1.0 or t <= 0.0:
                continue
            hit_x = rx + vx * t
            hit_y = ry + vy * t
            if hit_x * hit_x + hit_y * hit_y > 200.0**2:
                continue
            closest_t = t
            best_vel = (vx, vy)

        if best_vel is not None:
            perp = (-best_vel[1], best_vel[0])
            norm = math.hypot(*perp) or 1.0
            dodge = (perp[0] / norm, perp[1] / norm)
        else:
            dodge = (-direction[1], direction[0])

        combined = (
            direction[0] + self.dodge_bias * dodge[0],
            direction[1] + self.dodge_bias * dodge[1],
        )
        norm = math.hypot(*combined) or 1.0
        accel = (combined[0] / norm * 400.0, combined[1] / norm * 400.0)
        fire = dist <= 150 and direction[0] * face[0] + direction[1] * face[1] >= cos_thresh
        return accel, fire

    def _kiter(
        self,
        direction: Vec2,
        dist: float,
        face: Vec2,
        cos_thresh: float,
        projectile_speed: float | None,
    ) -> tuple[Vec2, bool]:
        """Keep distance while staying within weapon range."""

        if projectile_speed and projectile_speed > 0.0:
            desired = projectile_speed * self.desired_dist_factor
            fire_range = projectile_speed * self.fire_range_factor
        else:
            desired = 250.0 * (self.desired_dist_factor / 0.5)
            fire_range = 300.0 * (self.fire_range_factor / 0.8)

        accel: Vec2 = (0.0, 0.0)
        if dist < desired:
            accel = (-direction[0] * 400.0, -direction[1] * 400.0)
        elif dist > fire_range:
            accel = (direction[0] * 400.0, direction[1] * 400.0)

        fire = dist <= fire_range and direction[0] * face[0] + direction[1] * face[1] >= cos_thresh
        return accel, fire


def policy_for_weapon(weapon_name: str) -> SimplePolicy:
    """Return a :class:`SimplePolicy` tuned for ``weapon_name``.

    Bazooka users favour a kiting style, keeping more distance before
    firing. Knife wielders remain aggressive but give more weight to
    projectile dodging.
    """

    if weapon_name == "bazooka":
        return SimplePolicy(
            "kiter",
            desired_dist_factor=0.8,
            fire_range_factor=1.0,
        )
    if weapon_name == "knife":
        return SimplePolicy("aggressive", dodge_bias=1.0)
    return SimplePolicy("aggressive")
