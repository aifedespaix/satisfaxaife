"""Utility helpers for weapon metadata."""

from __future__ import annotations

import math

from app.core.types import EntityId

from . import weapon_registry
from .base import RangeType, WorldView


def range_type_for(name: str) -> RangeType:
    """Return the :class:`RangeType` for a registered weapon.

    Parameters
    ----------
    name:
        Identifier of the weapon in :mod:`app.weapons.weapon_registry`.

    Raises
    ------
    UnknownWeaponError
        If ``name`` is not associated with a registered weapon.
    """

    factory = weapon_registry.factory(name)
    range_type: RangeType = getattr(factory, "range_type", "contact")
    return range_type


CRITICAL_SPEED: float = 600.0
"""Minimum speed to trigger a critical hit."""

CRITICAL_MULTIPLIER: float = 2.0
"""Damage multiplier applied on critical hits."""


def critical_multiplier(view: WorldView, owner: EntityId) -> float:
    """Return the damage multiplier for ``owner`` based on current speed.

    A critical hit is triggered when the owner's speed exceeds
    :data:`CRITICAL_SPEED` and doubles the damage dealt.
    """

    vx, vy = view.get_velocity(owner)
    speed = math.hypot(vx, vy)
    return CRITICAL_MULTIPLIER if speed >= CRITICAL_SPEED else 1.0
