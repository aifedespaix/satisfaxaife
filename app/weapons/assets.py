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
