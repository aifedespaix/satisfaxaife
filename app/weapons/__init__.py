"""Weapon plugins."""

from app.core.registry import Registry

from .base import Weapon

weapon_registry: Registry[Weapon] = Registry()

# Import weapon modules to register them
from . import katana as _katana  # noqa: F401,E402
from . import shuriken as _shuriken  # noqa: F401,E402

__all__ = ["Weapon", "weapon_registry"]
