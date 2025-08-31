from __future__ import annotations

import math

__all__ = [
    "linear",
    "ease_in_out_cubic",
    "ease_out_back",
    "ease_out_elastic",
]


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """Clamp ``value`` within the inclusive range ``[minimum, maximum]``."""
    return max(minimum, min(value, maximum))


def linear(t: float) -> float:
    """Return ``t`` unchanged after clamping to ``[0.0, 1.0]``.

    Parameters
    ----------
    t:
        Progress ratio to interpolate.

    Returns
    -------
    float
        The clamped progress value in ``[0.0, 1.0]``.
    """

    return _clamp(t)


def ease_in_out_cubic(t: float) -> float:
    """Cubic easing accelerating then decelerating symmetrically.

    Parameters
    ----------
    t:
        Progress ratio to transform.

    Returns
    -------
    float
        Eased progress in ``[0.0, 1.0]``.
    """

    t = _clamp(t)
    if t < 0.5:
        return 4.0 * t**3
    return 1.0 - (-2.0 * t + 2.0) ** 3 / 2.0


def ease_out_back(t: float) -> float:
    """Easing with an overshoot going slightly past the target.

    Parameters
    ----------
    t:
        Progress ratio to transform.

    Returns
    -------
    float
        Eased progress in ``[0.0, 1.0]`` including a back overshoot.
    """

    t = _clamp(t)
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2


def ease_out_elastic(t: float) -> float:
    """Elastic easing producing a spring-like overshoot.

    Parameters
    ----------
    t:
        Progress ratio to transform.

    Returns
    -------
    float
        Eased progress in ``[0.0, 1.0]`` with oscillation.
    """

    t = _clamp(t)
    if t == 0.0 or t == 1.0:
        return t
    c4 = (2.0 * math.pi) / 3.0
    return math.pow(2.0, -10.0 * t) * math.sin((t * 10.0 - 0.75) * c4) + 1.0
