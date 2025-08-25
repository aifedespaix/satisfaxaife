from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from app.core.types import EntityId, Vec2
from app.weapons.base import WorldView


@dataclass(slots=True)
class SimplePolicy:
    """Very small deterministic combat policy."""

    style: Literal["aggressive", "kiter"]
    vertical_offset: float = 0.1

    def decide(self, me: EntityId, view: WorldView) -> tuple[Vec2, Vec2, bool]:
        """Return acceleration, facing vector and fire decision."""
        enemy = view.get_enemy(me)
        assert enemy is not None
        my_pos = view.get_position(me)
        enemy_pos = view.get_position(enemy)
        dx = enemy_pos[0] - my_pos[0]
        dy = enemy_pos[1] - my_pos[1]
        dist = math.hypot(dx, dy)
        direction = (dx / dist, dy / dist) if dist else (1.0, 0.0)
        my_health = view.get_health_ratio(me)

        accel: Vec2 = (0.0, 0.0)
        face: Vec2 = direction
        fire = False
        cos_thresh = math.cos(math.radians(18))

        if my_health < 0.15:
            accel = (-direction[0] * 400.0, -direction[1] * 400.0)
            return accel, face, fire

        if self.style == "aggressive":
            accel = (direction[0] * 400.0, direction[1] * 400.0)
            if dist <= 150 and direction[0] * face[0] + direction[1] * face[1] >= cos_thresh:
                fire = True
        else:  # kiter
            desired = 250.0
            if dist < desired:
                accel = (-direction[0] * 400.0, -direction[1] * 400.0)
            elif dist > desired + 50:
                accel = (direction[0] * 400.0, direction[1] * 400.0)
            face = direction
            if dist <= 300 and direction[0] * face[0] + direction[1] * face[1] >= cos_thresh:
                fire = True

        if abs(dy) <= 1e-6:
            offset_face = (direction[0], self.vertical_offset)
            norm = math.hypot(*offset_face) or 1.0
            face = (offset_face[0] / norm, offset_face[1] / norm)

        return accel, face, fire
