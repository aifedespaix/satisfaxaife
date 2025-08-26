from __future__ import annotations

import os
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
    if not pygame.get_init():
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))

    image = pygame.image.load((ASSET_DIR / name).as_posix()).convert_alpha()
    if scale != 1.0:
        size = (int(image.get_width() * scale), int(image.get_height() * scale))
        image = pygame.transform.smoothscale(image, size)
    return image
