from __future__ import annotations

import pygame

from app.render.sprites import load_sprite


def load_weapon_sprite(
    name: str,
    *,
    scale: float = 1.0,
    max_dim: float | None = None,
) -> pygame.Surface:
    """Load the sprite for a weapon stored under ``assets/weapons/<name>/weapon.png``.

    Parameters
    ----------
    name:
        Identifier of the weapon whose sprite to load.
    scale:
        Optional scaling factor applied to the sprite.
    max_dim:
        If provided, resize the sprite so that its longest side equals
        ``max_dim`` while preserving aspect ratio. ``scale`` is ignored when
        ``max_dim`` is given.
    """
    path = f"weapons/{name}/weapon.png"
    return load_sprite(path, scale=scale, max_dim=max_dim)


def load_gravity_well_sprite() -> pygame.Surface:
    """Load the gravity well sprite or return a placeholder surface.

    The actual sprite asset is expected to live under
    ``assets/weapons/gravity_well/weapon.png`` but may not yet be available.
    Until the asset is provided a transparent placeholder surface is used so
    tests and development can proceed without missing file errors.
    """
    try:
        return load_weapon_sprite("gravity_well")
    except FileNotFoundError:
        return pygame.Surface((1, 1), pygame.SRCALPHA)
