from __future__ import annotations

import math

from app.core.config import settings
from app.core.types import Vec2


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp value within the inclusive range [minimum, maximum]."""
    return max(minimum, min(value, maximum))


def ease_out_quad(t: float) -> float:
    """Simple quadratic easing returning values in [0, 1]."""
    return 1 - (1 - t) * (1 - t)


def ping_pong(value: float, length: float = 1.0) -> float:
    """Return a value oscillating between ``0`` and ``length``.

    The function maps any input onto a triangular wave pattern. Values rise
    linearly from ``0`` up to ``length`` and then descend back to ``0``,
    repeating this cycle indefinitely.

    Parameters
    ----------
    value:
        Input value to transform.
    length:
        Maximum value of the wave. Must be positive.

    Returns
    -------
    float
        Oscillating value in ``[0, length]``.

    Raises
    ------
    ValueError
        If ``length`` is not positive.
    """

    if length <= 0.0:
        raise ValueError("length must be positive")

    cycle = math.fmod(value, length * 2.0)
    if cycle < 0.0:
        cycle += length * 2.0
    return length - abs(cycle - length)


def to_screen(position: Vec2) -> tuple[int, int]:
    """Convert world coordinates to screen coordinates."""
    x, y = position
    return int(x), int(settings.height - y)
