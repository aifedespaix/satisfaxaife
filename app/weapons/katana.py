from __future__ import annotations

import math

from app.core.types import Damage, EntityId, Vec2

from . import weapon_registry
from .base import Weapon, WorldView


class Katana(Weapon):
    """Close-range melee weapon."""

    def __init__(self) -> None:
        super().__init__(name="katana", cooldown=0.6, damage=Damage(18), speed=0.0)

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:
        enemy = view.get_enemy(owner)
        if enemy is None:
            return
        owner_pos = view.get_position(owner)
        enemy_pos = view.get_position(enemy)
        dx = enemy_pos[0] - owner_pos[0]
        dy = enemy_pos[1] - owner_pos[1]
        distance_sq = dx * dx + dy * dy
        if distance_sq > 140 * 140:
            return
        dist = math.sqrt(distance_sq)
        to_enemy = (dx / dist, dy / dist)
        dot = to_enemy[0] * direction[0] + to_enemy[1] * direction[1]
        if dot < math.cos(math.radians(35)):
            return
        view.deal_damage(enemy, self.damage)
        knock = (to_enemy[0] * 220.0, to_enemy[1] * 220.0)
        view.apply_impulse(enemy, *knock)


weapon_registry.register("katana", Katana)
