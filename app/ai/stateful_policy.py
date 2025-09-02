"""Stateful AI policy with attack, dodge, parry and retreat states."""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from app.ai.policy import (
    SimplePolicy,
    _lead_target,
    _new_rng,
    _projectile_dodge,
)
from app.core.types import Damage, EntityId, Vec2
from app.weapons.base import RangeType, WorldView
from app.weapons.utils import range_type_for


class State(Enum):
    """Internal high-level behaviours for :class:`StatefulPolicy`."""

    ATTACK = "attack"
    DODGE = "dodge"
    PARRY = "parry"
    RETREAT = "retreat"


class Mode(Enum):
    """Overall tactical mode of :class:`StatefulPolicy`."""

    DEFENSIVE = "defensive"
    OFFENSIVE = "offensive"


@dataclass(slots=True)
class StatefulPolicy(SimplePolicy):
    """Finite state policy handling basic combat behaviours.

    The policy starts in :class:`State.ATTACK` and transitions to other states
    based on health and incoming threats. It reuses the motion primitives of
    :class:`app.ai.policy.SimplePolicy` but exposes clearer state specific
    methods to ease future extensions. Dodging mixes projectile avoidance with a
    random bias derived from the policy's pseudo-random generator, making the
    evasive path dependent on the initial seed while remaining reproducible.
    """

    state: State = State.ATTACK
    transition_time: float = 0.0
    parry_window: float = 0.15
    _incoming_time: float = field(default=float("inf"), init=False)

    def decide(  # type: ignore[override]
        self,
        me: EntityId,
        view: WorldView,
        now: float,
        projectile_speed: float | None = None,
    ) -> tuple[Vec2, Vec2, bool, bool]:
        """Return acceleration, facing vector, fire and parry decisions.

        The behaviour switches from defensive to offensive at
        ``transition_time``. In defensive mode the agent keeps its distance
        using :meth:`_evader`. Once offensive, the original state machine is
        employed.
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

        face: Vec2 = _lead_target(my_pos, enemy_pos, enemy_vel, projectile_speed or 0.0)
        cos_thresh = math.cos(math.radians(18))

        mode = Mode.DEFENSIVE if now < self.transition_time else Mode.OFFENSIVE

        if mode is Mode.DEFENSIVE:
            accel, fire = self._evader(
                me, view, my_pos, direction, dist, face, cos_thresh, projectile_speed
            )
            parry = False
        else:
            my_health = view.get_health_ratio(me)
            enemy_health = view.get_health_ratio(enemy)
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
                    style,
                    me,
                    view,
                    my_pos,
                    direction,
                    dist,
                    face,
                    cos_thresh,
                    projectile_speed,
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
                    style,
                    me,
                    view,
                    my_pos,
                    direction,
                    dist,
                    face,
                    cos_thresh,
                    projectile_speed,
                )
                accel = (-direction[0] * 400.0, -direction[1] * 400.0)
                parry = False

        if abs(dy) <= 1e-6:
            offset = self.vertical_offset + self.rng.uniform(-0.05, 0.05)
            offset_face = (direction[0], offset)
            norm = math.hypot(*offset_face) or 1.0
            face = (offset_face[0] / norm, offset_face[1] / norm)

        return accel, face, fire, parry

    def dash_direction(
        self,
        me: EntityId,
        view: WorldView,
        now: float,
        can_dash: Callable[[float], bool],
    ) -> Vec2 | None:
        """Return dash vector based on ``mode`` and weapon range.

        For contact weapons the dash orientation depends on the tactical mode:

        - Offensive mode dashes toward the enemy to engage in melee.
        - Defensive mode dashes away from the enemy while factoring in incoming
          projectiles.

        Non-contact weapons fall back to :class:`SimplePolicy` behaviour.
        """

        if self.range_type != "contact":
            return super().dash_direction(me, view, now, can_dash)
        if not can_dash(now):
            return None

        enemy = view.get_enemy(me)
        if enemy is None:
            return None

        my_pos = view.get_position(me)
        enemy_pos = view.get_position(enemy)
        dx = enemy_pos[0] - my_pos[0]
        dy = enemy_pos[1] - my_pos[1]
        dist = math.hypot(dx, dy)
        direction = (dx / dist, dy / dist) if dist > 1e-6 else (1.0, 0.0)

        mode = Mode.DEFENSIVE if now < self.transition_time else Mode.OFFENSIVE
        if mode is Mode.OFFENSIVE:
            return direction

        # Defensive mode --------------------------------------------------
        super_dir = super().dash_direction(me, view, now, can_dash)
        projectile_threat = super_dir is not None
        if dist > 150.0 and not projectile_threat:
            return None
        dodge = _projectile_dodge(me, view, my_pos, direction) if projectile_threat else (0.0, 0.0)
        away = (-direction[0], -direction[1])
        combined = (
            away[0] + self.dodge_bias * dodge[0],
            away[1] + self.dodge_bias * dodge[1],
        )
        norm = math.hypot(*combined) or 1.0
        return (combined[0] / norm, combined[1] / norm)

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
        """Return acceleration prioritising lateral evasion.

        The dodge vector is influenced by the random number generator to ensure
        distinct yet reproducible manoeuvres for different seeds.
        """

        raw_dodge = _projectile_dodge(me, view, my_pos, direction)
        dodge = self._smooth_dodge(raw_dodge)
        bias = self.dodge_bias + self.rng.uniform(-0.1, 0.1)
        combined = (
            direction[0] + bias * dodge[0],
            direction[1] + bias * dodge[1],
        )
        norm = math.hypot(*combined) or 1.0
        accel = (combined[0] / norm * 400.0, combined[1] / norm * 400.0)
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
    weapon_name: str,
    enemy_weapon_name: str,
    transition_time: float,
    rng: random.Random | None = None,
) -> StatefulPolicy:
    """Return a :class:`StatefulPolicy` tuned for a weapon matchup."""

    rng = rng or _new_rng()
    my_range: RangeType = range_type_for(weapon_name)
    enemy_range: RangeType = range_type_for(enemy_weapon_name)

    if my_range == "distant":
        style: Literal["evader", "kiter"] = "evader" if enemy_range == "contact" else "kiter"
        fire_factor = 0.0 if style == "evader" else float("inf")
        return StatefulPolicy(
            style,
            range_type=my_range,
            transition_time=transition_time,
            fire_range_factor=fire_factor,
            rng=rng,
        )

    return StatefulPolicy(
        "aggressive",
        range_type=my_range,
        transition_time=transition_time,
        rng=rng,
    )
