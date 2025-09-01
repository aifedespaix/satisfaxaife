"""Stateful AI policy with attack, dodge, parry and retreat states."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

import random

from app.ai.policy import (
    SimplePolicy,
    _lead_target,
    _new_rng,
    _projectile_dodge,
)
from app.core.types import Damage, EntityId, Vec2
from app.weapons.base import WorldView


class State(Enum):
    """Possible high-level behaviours for :class:`StatefulPolicy`."""

    ATTACK = "attack"
    DODGE = "dodge"
    PARRY = "parry"
    RETREAT = "retreat"


@dataclass(slots=True)
class StatefulPolicy(SimplePolicy):
    """Finite state policy handling basic combat behaviours.

    The policy starts in :class:`State.ATTACK` and transitions to other states
    based on health and incoming threats. It reuses the motion primitives of
    :class:`app.ai.policy.SimplePolicy` but exposes clearer state specific
    methods to ease future extensions.
    """

    state: State = State.ATTACK
    parry_window: float = 0.15
    _incoming_time: float = field(default=float("inf"), init=False)

    def decide(
        self, me: EntityId, view: WorldView, projectile_speed: float | None = None
    ) -> tuple[Vec2, Vec2, bool, bool]:
        """Return acceleration, facing vector, fire and parry decisions."""

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
        if my_health < 0.15 and not both_critical:
            self.state = State.RETREAT
        else:
            vel, t_hit = self._incoming_projectile(me, view, my_pos)
            self._incoming_time = t_hit
            if vel is not None and t_hit <= self.parry_window:
                self.state = State.PARRY
            elif vel is not None:
                self.state = State.DODGE
            else:
                self.state = State.ATTACK

        style = "aggressive" if both_critical else self.style

        if self.state == State.ATTACK:
            accel, fire = self._attack(
                style, me, view, my_pos, direction, dist, face, cos_thresh, projectile_speed
            )
            parry = False
        elif self.state == State.DODGE:
            accel, fire = self._dodge(me, view, my_pos, direction)
            parry = False
        elif self.state == State.PARRY:
            accel, fire = self._parry(direction)
            parry = True
        else:  # retreat
            # Fire decision still follows attack logic
            _, fire = self._attack(
                style, me, view, my_pos, direction, dist, face, cos_thresh, projectile_speed
            )
            accel = (-direction[0] * 400.0, -direction[1] * 400.0)
            parry = False

        if abs(dy) <= 1e-6:
            offset_face = (direction[0], self.vertical_offset)
            norm = math.hypot(*offset_face) or 1.0
            face = (offset_face[0] / norm, offset_face[1] / norm)

        return accel, face, fire, parry

    # State handlers -----------------------------------------------------
    def _attack(
        self,
        style: Literal["aggressive", "kiter", "evader"],
        me: EntityId,
        view: WorldView,
        my_pos: Vec2,
        direction: Vec2,
        dist: float,
        face: Vec2,
        cos_thresh: float,
        projectile_speed: float | None,
    ) -> tuple[Vec2, bool]:
        if style == "aggressive":
            return self._aggressive(me, view, my_pos, direction, dist, face, cos_thresh)
        if style == "evader":
            return self._evader(
                me, view, my_pos, direction, dist, face, cos_thresh, projectile_speed
            )
        return self._kiter(direction, dist, face, cos_thresh, projectile_speed)

    def _dodge(
        self,
        me: EntityId,
        view: WorldView,
        my_pos: Vec2,
        direction: Vec2,
    ) -> tuple[Vec2, bool]:
        dodge = _projectile_dodge(me, view, my_pos, direction)
        accel = (dodge[0] * 400.0, dodge[1] * 400.0)
        return accel, False

    def _parry(self, direction: Vec2) -> tuple[Vec2, bool]:
        # Stand still and face the threat; firing is disabled
        accel = (0.0, 0.0)
        return accel, False

    # Utilities ----------------------------------------------------------
    def _incoming_projectile(
        self, me: EntityId, view: WorldView, position: Vec2
    ) -> tuple[Vec2 | None, float]:
        closest_t = float("inf")
        best_vel: Vec2 | None = None
        for proj in view.iter_projectiles(excluding=me):
            px, py = proj.position
            vx, vy = proj.velocity
            rx = px - position[0]
            ry = py - position[1]
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
        return best_vel, closest_t

    def parry_damage(self, damage: Damage) -> Damage:
        """Return modified ``damage`` after a parry attempt."""
        if self.state == State.PARRY and self._incoming_time <= self.parry_window:
            return Damage(0.0)
        return damage


def policy_for_weapon(
    weapon_name: str, rng: random.Random | None = None
) -> StatefulPolicy:
    """Return a :class:`StatefulPolicy` tuned for ``weapon_name``.

    Parameters
    ----------
    weapon_name:
        Identifier of the weapon used by the agent.
    rng:
        Optional random number generator. When ``None``, a new instance
        derived from the global seed is created.
    """

    rng = rng or _new_rng()
    if weapon_name == "bazooka":
        return StatefulPolicy(
            "evader",
            desired_dist_factor=1.2,
            fire_range_factor=1.2,
            rng=rng,
        )
    if weapon_name == "knife":
        return StatefulPolicy("aggressive", dodge_bias=1.0, rng=rng)
    if weapon_name == "shuriken":
        return StatefulPolicy("aggressive", fire_range=float("inf"), rng=rng)
    return StatefulPolicy("aggressive", rng=rng)
