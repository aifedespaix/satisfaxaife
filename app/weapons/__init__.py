"""Weapon plugins and registry.

Third-party packages can extend the game by registering new weapons::

    from app.weapons import weapon_registry, Weapon

    class MyWeapon(Weapon):
        ...

    weapon_registry.register("my_weapon", MyWeapon)

All modules importing this package will automatically discover registered
weapons.
"""

from app.core.registry import Registry

from .base import Weapon

weapon_registry: Registry[Weapon] = Registry()

# Import weapon modules to register them
from . import katana as _katana  # noqa: F401,E402
from . import orbital as _orbital  # noqa: F401,E402
from . import shuriken as _shuriken  # noqa: F401,E402

__all__ = ["Weapon", "weapon_registry"]
