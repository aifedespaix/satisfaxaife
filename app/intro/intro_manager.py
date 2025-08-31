from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

from app.core.config import settings
from app.core.types import Vec2
from app.core.utils import clamp, ease_out_quad
from app.render.intro_renderer import IntroRenderer

if TYPE_CHECKING:  # pragma: no cover - hints only
    import pygame


Easing = Callable[[float], float]


def ease_out_back(t: float) -> float:
    """Return an easing with a small overshoot for a bounce effect."""
    c1 = 1.70158
    c3 = c1 + 1.0
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def pulse_ease(t: float) -> float:
    """Return a pulsating value between 0 and 1."""
    return 0.5 - 0.5 * math.cos(t * math.tau)


@dataclass(frozen=True)
class IntroConfig:
    """Configuration for intro timings, positions and effects.

    The default values mimic the previous hard coded behaviour where elements
    slide in from half the screen width and end up at the quarter positions.

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
        rendering. They allow simple customisation of element sizes.
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


class IntroState(Enum):
    """All states of the introduction sequence."""

    IDLE = auto()
    LOGO_IN = auto()
    WEAPONS_IN = auto()
    HOLD = auto()
    FADE_OUT = auto()
    DONE = auto()


class IntroManager:
    """Manage the pre-match introduction sequence."""

    def __init__(
        self,
        config: IntroConfig | None = None,
        intro_renderer: IntroRenderer | None = None,
        *,
        allow_skip: bool = True,
        skip_key: int | None = None,
    ) -> None:
        import pygame

        self.config = config or IntroConfig()
        self._renderer = intro_renderer or IntroRenderer(
            settings.width, settings.height, self.config
        )
        self.allow_skip = allow_skip
        self.skip_key = skip_key if skip_key is not None else pygame.K_ESCAPE
        self._state = IntroState.IDLE
        self._elapsed = 0.0

    @property
    def state(self) -> IntroState:
        """Return current state of the intro."""

        return self._state

    def start(self) -> None:
        """Start the intro sequence."""

        self._state = IntroState.LOGO_IN
        self._elapsed = 0.0

    def update(self, dt: float, events: Sequence[pygame.event.Event] | None = None) -> None:
        """Advance the intro state machine.

        Parameters
        ----------
        dt:
            Delta time in seconds.
        events:
            Optional iterable of pygame events used to handle skipping.
        """

        if self._state is IntroState.DONE:
            return

        if self.allow_skip and events:
            import pygame

            for event in events:
                if (
                    getattr(event, "type", None) == pygame.KEYDOWN
                    and getattr(event, "key", None) == self.skip_key
                ):
                    self._state = IntroState.DONE
                    return

        self._elapsed += dt
        if self._elapsed >= self._current_duration():
            self._advance_state()

    def draw(
        self, surface: pygame.Surface, labels: tuple[str, str]
    ) -> None:  # pragma: no cover - visual
        """Render the intro on ``surface`` using the configured renderer."""

        progress = self._progress()
        self._renderer.draw(surface, labels, progress)

    def is_finished(self) -> bool:
        """Return ``True`` if the intro has completed."""

        return self._state is IntroState.DONE

    # internal helpers -----------------------------------------------------
    def _current_duration(self) -> float:
        return {
            IntroState.LOGO_IN: self.config.logo_in,
            IntroState.WEAPONS_IN: self.config.weapons_in,
            IntroState.HOLD: self.config.hold,
            IntroState.FADE_OUT: self.config.fade_out,
        }.get(self._state, 0.0)

    def _advance_state(self) -> None:
        self._elapsed = 0.0
        self._state = {
            IntroState.LOGO_IN: IntroState.WEAPONS_IN,
            IntroState.WEAPONS_IN: IntroState.HOLD,
            IntroState.HOLD: IntroState.FADE_OUT,
            IntroState.FADE_OUT: IntroState.DONE,
        }.get(self._state, IntroState.DONE)

    def _state_progress(self) -> float:
        duration = self._current_duration()
        if duration == 0.0:
            return 1.0
        return clamp(self._elapsed / duration, 0.0, 1.0)

    def _progress(self) -> float:
        t = self._state_progress()
        if self._state is IntroState.LOGO_IN:
            return self.config.micro_bounce(t)
        if self._state is IntroState.WEAPONS_IN:
            return self.config.pulse(t)
        if self._state is IntroState.HOLD:
            return 1.0
        if self._state is IntroState.FADE_OUT:
            return 1.0 - self.config.fade(t)
        if self._state is IntroState.DONE:
            return 0.0
        return 0.0
