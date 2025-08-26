from __future__ import annotations

from functools import cache
from pathlib import Path

import pygame

ASSET_DIR = Path(__file__).resolve().parents[2] / "assets"


@cache
def load_sprite(name: str, scale: float = 1.0) -> pygame.Surface:
    """Load and cache a sprite from the assets directory.

    Parameters
    ----------
    name:
        File name within the ``assets`` directory.
    scale:
        Optional scaling factor applied to the loaded image.
    """
    image = pygame.image.load((ASSET_DIR / name).as_posix()).convert_alpha()
    if scale != 1.0:
        size = (int(image.get_width() * scale), int(image.get_height() * scale))
        image = pygame.transform.smoothscale(image, size)
    return image
