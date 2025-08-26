from __future__ import annotations

import os
from functools import cache
from pathlib import Path

import pygame

ASSET_DIR = Path(__file__).resolve().parents[2] / "assets"


@cache
def load_sprite(name: str, scale: float = 1.0, max_dim: float | None = None) -> pygame.Surface:
    """Load and cache a sprite from the assets directory.

    Parameters
    ----------
    name:
        File name within the ``assets`` directory.
    scale:
        Optional scaling factor applied to the loaded image.
    max_dim:
        If provided, resize the image so that its longest side equals ``max_dim``
        while preserving aspect ratio. ``scale`` is ignored when ``max_dim`` is
        given.
    """
    if not pygame.get_init():
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()
    if pygame.display.get_surface() is None:
        pygame.display.set_mode((1, 1))

    image = pygame.image.load((ASSET_DIR / name).as_posix()).convert_alpha()
    if max_dim is not None:
        width, height = image.get_size()
        factor = max_dim / float(max(width, height))
        new_size = (int(width * factor), int(height * factor))
        image = pygame.transform.smoothscale(image, new_size)
    elif scale != 1.0:
        width, height = image.get_size()
        new_size = (int(width * scale), int(height * scale))
        image = pygame.transform.smoothscale(image, new_size)
    return image
