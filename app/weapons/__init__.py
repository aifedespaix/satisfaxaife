"""Weapon plugins and registry.

Third-party packages can extend the game by registering new weapons::

    from app.weapons import weapon_registry, Weapon

    class MyWeapon(Weapon):
        ...

    weapon_registry.register("my_weapon", MyWeapon)

All modules importing this package will automatically discover registered
weapons.
"""

from contextlib import suppress

from app.core.registry import Registry

from .base import Weapon

weapon_registry: Registry[Weapon] = Registry()

# Import weapon modules to register them

with suppress(Exception):  # pragma: no cover - optional weapons may have extra deps
    from . import bazooka as _bazooka  # noqa: F401,E402
with suppress(Exception):  # pragma: no cover
    from . import katana as _katana  # noqa: F401,E402
with suppress(Exception):  # pragma: no cover
    from . import knife as _knife  # noqa: F401,E402
with suppress(Exception):  # pragma: no cover
    from . import shuriken as _shuriken  # noqa: F401,E402

__all__ = ["Weapon", "weapon_registry"]
