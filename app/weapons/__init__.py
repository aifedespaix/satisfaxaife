"""Weapon plugins and registry.

Third-party packages can extend the game by registering new weapons::

    from app.weapons import weapon_registry, Weapon

    class MyWeapon(Weapon):
        ...

    weapon_registry.register("my_weapon", MyWeapon)

All modules importing this package will automatically discover registered
weapons.
"""

import logging

from app.core.registry import Registry

from .base import Weapon

weapon_registry: Registry[Weapon] = Registry()

# Import weapon modules to register them
logger = logging.getLogger(__name__)

try:
    from . import bazooka as _bazooka  # noqa: F401,E402
except Exception as exc:  # pragma: no cover - optional weapons may have extra deps
    logger.warning("Failed to import optional weapon module 'bazooka': %s", exc)

try:
    from . import katana as _katana  # noqa: F401,E402
except Exception as exc:  # pragma: no cover
    logger.warning("Failed to import optional weapon module 'katana': %s", exc)

try:
    from . import knife as _knife  # noqa: F401,E402
except Exception as exc:  # pragma: no cover
    logger.warning("Failed to import optional weapon module 'knife': %s", exc)

try:
    from . import shuriken as _shuriken  # noqa: F401,E402
except Exception as exc:  # pragma: no cover
    logger.warning("Failed to import optional weapon module 'shuriken': %s", exc)

try:
    from . import gravity_well as _gravity_well  # noqa: F401,E402
except Exception as exc:  # pragma: no cover
    logger.warning("Failed to import optional weapon module 'gravity_well': %s", exc)

try:
    from . import resonance_hammer as _resonance_hammer  # noqa: F401,E402
except Exception as exc:  # pragma: no cover
    logger.warning("Failed to import optional weapon module 'resonance_hammer': %s", exc)

__all__ = ["Weapon", "weapon_registry"]
