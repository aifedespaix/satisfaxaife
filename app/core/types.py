from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

Vec2 = tuple[float, float]
Color = tuple[int, int, int]


@dataclass(slots=True)
class Stats:
    """Base statistics for an entity."""

    max_health: float
    max_speed: float


@dataclass(frozen=True, slots=True)
class Damage:
    """Represents raw damage dealt to an entity."""

    amount: float


@dataclass(frozen=True, slots=True)
class EntityId:
    """Unique identifier for game entities."""

    value: int


@dataclass(slots=True)
class ProjectileInfo:
    """Snapshot of a projectile exposed to AI policies."""

    owner: EntityId
    position: Vec2
    velocity: Vec2


WeaponFactory = NewType("WeaponFactory", object)
TeamId = NewType("TeamId", int)
