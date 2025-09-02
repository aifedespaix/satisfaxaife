"""Weapon plugins and registry.

Third-party packages can extend the game by registering new weapons::

    from app.weapons import weapon_registry, Weapon

    class MyWeapon(Weapon):
        ...

    weapon_registry.register("my_weapon", MyWeapon)

All modules importing this package will automatically discover registered
weapons.
"""

from __future__ import annotations

import importlib
import logging

from app.core.registry import Registry

from .base import Weapon

weapon_registry: Registry[Weapon] = Registry()

# Import weapon modules to register them
logger = logging.getLogger(__name__)

_OPTIONAL_MODULES: list[str] = [
    "bazooka",
    "katana",
    "knife",
    "shuriken",
    "gravity_well",
    "resonance_hammer",
]

for _module in _OPTIONAL_MODULES:
    try:
        importlib.import_module(f"{__name__}.{_module}")
    except Exception as exc:  # pragma: no cover - optional weapons may have extra deps
        logger.warning("Failed to import optional weapon module '%s': %s", _module, exc)

__all__ = ["Weapon", "weapon_registry"]
