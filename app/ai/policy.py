from __future__ import annotations

import math
from dataclasses import dataclass, field
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


def _projectile_dodge(me: EntityId, view: WorldView, position: Vec2, direction: Vec2) -> Vec2:
    """Return a unit vector helping ``me`` dodge incoming projectiles.

    Every projectile within a one second horizon is evaluated. A repulsive
    vector pointing away from the predicted closest point of each projectile is
    accumulated and weighted by the inverse of the time to impact. The final
    dodge direction is the normalised sum of these vectors. If no projectile is
    threatening the returned vector is perpendicular to ``direction``.
    """

    dodge_x = 0.0
    dodge_y = 0.0
    for proj in view.iter_projectiles(excluding=me):
        px, py = proj.position
        vx, vy = proj.velocity
        rx = px - position[0]
        ry = py - position[1]
        speed_sq = vx * vx + vy * vy
        if speed_sq <= 1e-6:
            continue
        # Time until closest approach between projectile and agent.
        t = -(rx * vx + ry * vy) / speed_sq
        if t <= 0.0 or t > 1.0:
            continue
        cx = rx + vx * t
        cy = ry + vy * t
        if cx * cx + cy * cy > 200.0 ** 2:
            continue
        dist = math.hypot(cx, cy)
        if dist <= 1e-6:
            # When the predicted impact is at the current position fall back to a
            # perpendicular vector to the projectile velocity.
            perp_x, perp_y = -vy, vx
            dist = math.hypot(perp_x, perp_y) or 1.0
            rep_x = perp_x / dist
            rep_y = perp_y / dist
        else:
            rep_x = -cx / dist
            rep_y = -cy / dist
        weight = 1.0 / (t + 1e-3)
        dodge_x += rep_x * weight
        dodge_y += rep_y * weight

    if abs(dodge_x) > 1e-6 or abs(dodge_y) > 1e-6:
        norm = math.hypot(dodge_x, dodge_y) or 1.0
        return (dodge_x / norm, dodge_y / norm)

    perp = (-direction[1], direction[0])
    norm = math.hypot(*perp) or 1.0
    return (perp[0] / norm, perp[1] / norm)


@dataclass(slots=True)
class SimplePolicy:
    """Very small deterministic combat policy."""

    style: Literal["aggressive", "kiter", "evader"]
    vertical_offset: float = 0.1
    dodge_bias: float = 0.5
    dodge_smoothing: float = 0.5
    desired_dist_factor: float = 0.5
    fire_range_factor: float = 0.8
    fire_range: float = 150.0
    _prev_dodge: Vec2 = field(default=(1.0, 0.0), init=False, repr=False)

    def decide(
        self, me: EntityId, view: WorldView, projectile_speed: float | None = None
    ) -> tuple[Vec2, Vec2, bool, bool]:
        """Return acceleration, facing vector, fire and parry decisions.

        The agent retreats when its health falls below ``15%``. If both
        combatants are in this critical state the retreat is cancelled and the
        agent switches to an aggressive style for the remainder of the fight.
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
        enemy_health = view.get_health_ratio(enemy)

        face: Vec2 = _lead_target(my_pos, enemy_pos, enemy_vel, projectile_speed or 0.0)
        cos_thresh = math.cos(math.radians(18))

        both_critical = my_health < 0.15 and enemy_health < 0.15
        fleeing = my_health < 0.15 and not both_critical
        style = "aggressive" if both_critical else self.style

        if style == "aggressive":
            accel, fire = self._aggressive(me, view, my_pos, direction, dist, face, cos_thresh)
        elif style == "evader":
            accel, fire = self._evader(
                me, view, my_pos, direction, dist, face, cos_thresh, projectile_speed
            )
        else:
            accel, fire = self._kiter(direction, dist, face, cos_thresh, projectile_speed)

        if fleeing:
            accel = (-direction[0] * 400.0, -direction[1] * 400.0)

        if abs(dy) <= 1e-6:
            offset_face = (direction[0], self.vertical_offset)
            norm = math.hypot(*offset_face) or 1.0
            face = (offset_face[0] / norm, offset_face[1] / norm)

        return accel, face, fire, False

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

        raw_dodge = _projectile_dodge(me, view, my_pos, direction)
        dodge = self._smooth_dodge(raw_dodge)
        combined = (
            direction[0] + self.dodge_bias * dodge[0],
            direction[1] + self.dodge_bias * dodge[1],
        )
        norm = math.hypot(*combined) or 1.0
        accel = (combined[0] / norm * 400.0, combined[1] / norm * 400.0)
        fire = dist <= self.fire_range and direction[0] * face[0] + direction[1] * face[1] >= cos_thresh
        return accel, fire

    def _evader(
        self,
        me: EntityId,
        view: WorldView,
        my_pos: Vec2,
        direction: Vec2,
        dist: float,
        face: Vec2,
        cos_thresh: float,
        projectile_speed: float | None,
    ) -> tuple[Vec2, bool]:
        """Run away from the enemy while dodging projectiles."""

        raw_dodge = _projectile_dodge(me, view, my_pos, direction)
        dodge = self._smooth_dodge(raw_dodge)
        base = (-direction[0], -direction[1])
        combined = (
            base[0] + self.dodge_bias * dodge[0],
            base[1] + self.dodge_bias * dodge[1],
        )
        norm = math.hypot(*combined) or 1.0
        accel = (combined[0] / norm * 400.0, combined[1] / norm * 400.0)

        if projectile_speed and projectile_speed > 0.0:
            fire_range = projectile_speed * self.fire_range_factor
        else:
            fire_range = 300.0 * (self.fire_range_factor / 0.8)

        fire = dist >= fire_range and direction[0] * face[0] + direction[1] * face[1] >= cos_thresh
        return accel, fire

    def _smooth_dodge(self, raw: Vec2) -> Vec2:
        """Return a smoothed dodge vector.

        The smoothing factor ``dodge_smoothing`` controls how quickly the dodge
        direction reacts to changes. ``1.0`` disables smoothing while smaller
        values yield more inertia.
        """

        alpha = self.dodge_smoothing
        sx = alpha * raw[0] + (1.0 - alpha) * self._prev_dodge[0]
        sy = alpha * raw[1] + (1.0 - alpha) * self._prev_dodge[1]
        norm = math.hypot(sx, sy) or 1.0
        self._prev_dodge = (sx / norm, sy / norm)
        return self._prev_dodge

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

    Bazooka users adopt an evasive style, maximising distance and dodging
    incoming rockets. Knife wielders remain aggressive but give more weight to
    projectile dodging.
    """

    if weapon_name == "bazooka":
        return SimplePolicy(
            "evader",
            desired_dist_factor=1.2,
            fire_range_factor=1.2,
        )
    if weapon_name == "knife":
        return SimplePolicy("aggressive", dodge_bias=1.0)
    if weapon_name == "shuriken":
        return SimplePolicy("aggressive", fire_range=float("inf"))
    return SimplePolicy("aggressive")
