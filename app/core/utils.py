from __future__ import annotations

from app.core.config import settings
from app.core.types import Vec2


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp value within the inclusive range [minimum, maximum]."""
    return max(minimum, min(value, maximum))


def ease_out_quad(t: float) -> float:
    """Simple quadratic easing returning values in [0, 1]."""
    return 1 - (1 - t) * (1 - t)


def to_screen(position: Vec2) -> tuple[int, int]:
    """Convert world coordinates to screen coordinates."""
    x, y = position
    return int(x), int(settings.height - y)
