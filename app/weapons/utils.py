"""Utility helpers for weapon metadata."""

from __future__ import annotations

from . import weapon_registry
from .base import RangeType


def range_type_for(name: str) -> RangeType:
    """Return the :class:`RangeType` for a registered weapon.

    Parameters
    ----------
    name:
        Identifier of the weapon in :mod:`app.weapons.weapon_registry`.

    Raises
    ------
    KeyError
        If ``name`` is not associated with a registered weapon.
    """

    factory = weapon_registry.factory(name)
    range_type: RangeType = getattr(factory, "range_type", "contact")  # type: ignore[assignment]
    return range_type

