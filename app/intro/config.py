from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

from app.core.tween import ease_out_back
from app.core.types import Vec2
from app.core.utils import clamp, ease_out_quad

Easing = Callable[[float], float]

def monotone_pulse(t: float) -> float:
    """Return a monotonic easing curve for the weapon intro."""
    return ease_out_quad(clamp(t, 0.0, 1.0))


@dataclass(frozen=True, slots=True)
class IntroConfig:
    """Configuration for intro timings, assets and behaviour.

    Parameters
    ----------
    logo_in, weapons_in, hold, fade_out:
        Durations in seconds for each phase of the intro animation. Defaults to
        ``logo_in=0.0``, ``weapons_in=0.0``, ``hold=1.0`` and
        ``fade_out=0.25``.
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
    hold_float_amplitude, hold_float_frequency:
        Amplitude in pixels/degree and angular frequency in radians per second
        for the gentle floating effect applied during the ``HOLD`` phase.
    """

    logo_in: float = 0.0
    weapons_in: float = 0.0
    hold: float = 1.0
    fade_out: float = 0.25
    hold_float_amplitude: float = 5.0
    hold_float_frequency: float = 2.0
    micro_bounce: Easing = ease_out_back
    pulse: Easing = monotone_pulse
    fade: Easing = ease_out_quad
    left_pos_pct: Vec2 = (0.25, 0.6)
    right_pos_pct: Vec2 = (0.75, 0.6)
    center_pos_pct: Vec2 = (0.5, 0.45)
    slide_offset_pct: float = 0.5
    logo_scale: float = 1.0
    weapon_scale: float = 1.0
    font_path: Path | None = None
    logo_path: Path | None = None
    weapon_a_path: Path | None = None
    weapon_b_path: Path | None = None
    allow_skip: bool = True
    skip_key: int = 27


def set_intro_weapons(
    left: Path | None, right: Path | None, *, config: IntroConfig | None = None
) -> IntroConfig:
    """Return a copy of ``config`` with weapon image paths updated.

    Parameters
    ----------
    left, right:
        Paths to the images representing the left and right weapons.
    config:
        Optional base configuration to update. When ``None`` a default
        :class:`IntroConfig` is created.

    Returns
    -------
    IntroConfig
        A new configuration with ``weapon_a_path`` and ``weapon_b_path`` set
        to the provided values.
    """

    base = config or IntroConfig()
    return replace(base, weapon_a_path=left, weapon_b_path=right)


__all__ = ["IntroConfig", "set_intro_weapons"]
