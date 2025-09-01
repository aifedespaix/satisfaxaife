"""Utility classes and helpers for tests."""
from __future__ import annotations

import pygame

from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import WeaponEffect, WorldView
from app.world.entities import Ball


class StubWorldView(WorldView):
    """Minimal :class:`WorldView` implementation for physics tests."""

    def __init__(self, ball: Ball) -> None:
        self.ball = ball

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # pragma: no cover - unused
        return None

    def get_position(self, eid: EntityId) -> Vec2:
        pos = self.ball.body.position
        return (float(pos.x), float(pos.y))

    def get_velocity(self, eid: EntityId) -> Vec2:  # pragma: no cover - unused
        return (0.0, 0.0)

    def get_health_ratio(self, eid: EntityId) -> float:  # pragma: no cover - unused
        return 1.0

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:
        self.ball.take_damage(damage)

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # pragma: no cover - unused
        self.ball.body.apply_impulse_at_local_point((vx, vy))

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # pragma: no cover - unused
        pass

    def spawn_effect(self, effect: WeaponEffect) -> None:  # pragma: no cover - unused
        pass

    def spawn_projectile(
        self,
        owner: EntityId,
        position: Vec2,
        velocity: Vec2,
        radius: float,
        damage: Damage,
        knockback: float,
        ttl: float,
        sprite: pygame.Surface | None = None,
        spin: float = 0.0,
        trail_color: tuple[int, int, int] | None = None,
        acceleration: float = 0.0,
    ) -> WeaponEffect:  # pragma: no cover - unused
        raise NotImplementedError

    def iter_projectiles(
        self, excluding: EntityId | None = None
    ) -> list[ProjectileInfo]:  # pragma: no cover - unused
        return []
