from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from app.core.types import Vec2
from app.core.utils import ease_out_quad

Easing = Callable[[float], float]


def ease_out_back(t: float) -> float:
    """Return an easing with a small overshoot for a bounce effect."""
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def pulse_ease(t: float) -> float:
    """Return a pulsating value between 0 and 1."""
    import math

    return 0.5 - 0.5 * math.cos(t * math.tau)


@dataclass(frozen=True, slots=True)
class IntroConfig:
    """Configuration for intro timings, assets and behaviour.

    Parameters
    ----------
    logo_in, weapons_in, hold, fade_out:
        Durations in seconds for each phase of the intro animation.
    micro_bounce, pulse, fade:
        Easing functions used for the various phases.
    left_pos_pct, right_pos_pct, center_pos_pct:
        Final positions for the left label, right label and centre marker as
        percentages of the screen size.
    slide_offset_pct:
        Horizontal offset in percent of the screen width from which the labels
        start sliding.
    logo_scale, weapon_scale:
        Multiplicative factors applied to the logo and weapon images when
        rendering.
    font_path, logo_path, weapon_a_path, weapon_b_path:
        Paths to the font and images used by the introduction. When ``None`` or
        missing, fallbacks will be generated.
    allow_skip, skip_key:
        Options controlling whether the intro can be skipped and which key
        triggers the skip. ``skip_key`` defaults to the Escape key.
    """

    logo_in: float = 1.0
    weapons_in: float = 1.0
    hold: float = 1.0
    fade_out: float = 1.0
    micro_bounce: Easing = ease_out_back
    pulse: Easing = pulse_ease
    fade: Easing = ease_out_quad
    left_pos_pct: Vec2 = (0.25, 0.5)
    right_pos_pct: Vec2 = (0.75, 0.5)
    center_pos_pct: Vec2 = (0.5, 0.5)
    slide_offset_pct: float = 0.5
    logo_scale: float = 1.0
    weapon_scale: float = 1.0
    font_path: Path | None = None
    logo_path: Path | None = None
    weapon_a_path: Path | None = None
    weapon_b_path: Path | None = None
    allow_skip: bool = True
    skip_key: int = 27
