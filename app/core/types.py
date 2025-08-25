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


@dataclass(slots=True)
class Damage:
    """Represents raw damage dealt to an entity."""

    amount: float


@dataclass(frozen=True, slots=True)
class EntityId:
    """Unique identifier for game entities."""

    value: int


WeaponFactory = NewType("WeaponFactory", object)
