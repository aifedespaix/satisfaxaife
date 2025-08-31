from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .config import IntroConfig

if TYPE_CHECKING:  # pragma: no cover - hints only
    import pygame

FALLBACK_COLOR: tuple[int, int, int] = (255, 0, 255)
FALLBACK_SIZE: tuple[int, int] = (64, 64)


@dataclass(frozen=True, slots=True)
class IntroAssets:
    """Assets required by the intro sequence."""

    font: pygame.font.Font
    logo: pygame.Surface
    weapon_a: pygame.Surface
    weapon_b: pygame.Surface

    @classmethod
    def load(cls, config: IntroConfig, *, font_size: int = 72) -> IntroAssets:
        """Load assets defined in ``config`` using fallbacks when missing."""
        import pygame

        pygame.font.init()

        def _load_font(path: Path | None) -> pygame.font.Font:
            if path and Path(path).exists():
                return pygame.font.Font(str(path), font_size)
            logging.warning("Missing font at %s; using default font", path)
            return pygame.font.Font(None, font_size)

        font = _load_font(config.font_path)

        def _load_image(path: Path | None, label: str) -> pygame.Surface:
            if path and Path(path).exists():
                return pygame.image.load(str(path)).convert_alpha()
            logging.warning("Missing image at %s; using fallback", path)
            surface = pygame.Surface(FALLBACK_SIZE)
            surface.fill(FALLBACK_COLOR)
            text = font.render(label, True, (0, 0, 0))
            rect = text.get_rect(center=(FALLBACK_SIZE[0] // 2, FALLBACK_SIZE[1] // 2))
            surface.blit(text, rect)
            return surface

        logo = _load_image(config.logo_path, "logo")
        weapon_a = _load_image(config.weapon_a_path, "A")
        weapon_b = _load_image(config.weapon_b_path, "B")
        return cls(font=font, logo=logo, weapon_a=weapon_a, weapon_b=weapon_b)


__all__ = ["IntroAssets", "FALLBACK_COLOR", "FALLBACK_SIZE"]
