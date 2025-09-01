from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from app.core.animation import Animation, Timeline
from app.core.config import settings
from app.core.types import Vec2
from app.render.hud import Hud
from app.render.intro_renderer import IntroRenderer

from .assets import IntroAssets
from .config import IntroConfig

if TYPE_CHECKING:  # pragma: no cover - hints only
    from app.audio import AudioEngine


FIGHT_SOUND: str = "assets/fight.ogg"
WEAPON_PULSE_AMPLITUDE: float = 0.05


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
        engine: AudioEngine | None = None,
    ) -> None:
        self.config = config or IntroConfig()
        if self.config.logo_path is None or self.config.font_path is None:
            assets_dir = Path(__file__).resolve().parents[2] / "assets"
            updates: dict[str, Any] = {}
            if self.config.logo_path is None:
                updates["logo_path"] = assets_dir / "vs.png"
            if self.config.font_path is None:
                updates["font_path"] = assets_dir / "fonts" / "FightKickDemoRegular.ttf"
            self.config = replace(self.config, **updates)
        self.assets = IntroAssets.load(self.config)
        self._renderer = intro_renderer or IntroRenderer(
            settings.width, settings.height, self.config, assets=self.assets
        )
        self._engine = engine
        self._state = IntroState.IDLE
        self._states: list[IntroState] = [
            IntroState.LOGO_IN,
            IntroState.WEAPONS_IN,
            IntroState.HOLD,
            IntroState.FADE_OUT,
        ]
        self._state_index = 0
        self._timeline: Timeline | None = None
        self._elapsed = 0.0
        self._duration = (
            self.config.logo_in
            + self.config.weapons_in
            + self.config.hold
            + self.config.fade_out
        )
        self._targets: tuple[pygame.Rect, pygame.Rect, pygame.Rect] | None = None

    @property
    def state(self) -> IntroState:
        """Return current state of the intro."""

        return self._state

    def start(self) -> None:
        """Start the intro sequence if idle.

        The associated :class:`~app.render.intro_renderer.IntroRenderer` is
        reset to clear any cached positions. Calling :meth:`start` while the
        introduction is already running or has completed has no effect. This
        guards against unintended resets when the caller triggers ``start``
        multiple times.
        """

        if self._state is not IntroState.IDLE:
            return
        self._state = IntroState.LOGO_IN
        self._state_index = 0
        self._elapsed = 0.0
        self._targets = None
        self._renderer.reset()
        self._timeline = Timeline()
        self._timeline.add(Animation(0.0, 1.0, self.config.logo_in))
        self._timeline.add(Animation(0.0, 1.0, self.config.weapons_in))
        self._timeline.add(Animation(0.0, 1.0, self.config.hold))
        self._timeline.add(Animation(0.0, 1.0, self.config.fade_out))

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

        if self.config.allow_skip and events:
            import pygame

            for event in events:
                if (
                    getattr(event, "type", None) == pygame.KEYDOWN
                    and getattr(event, "key", None) == self.config.skip_key
                ):
                    self._timeline.cancel() if self._timeline else None
                    self._state = IntroState.DONE
                    return

        timeline = self._timeline
        if timeline is None:
            return

        prev_state = self._state
        prev_anim = timeline.current
        timeline.update(dt)
        current = timeline.current

        if timeline.finished:
            self._state = IntroState.DONE
            return

        if current is not prev_anim:
            self._state_index += 1
            self._state = self._states[self._state_index]
            if prev_state is IntroState.HOLD and self._state is IntroState.FADE_OUT:
                timestamp = self.config.logo_in + self.config.weapons_in + self.config.hold
                engine = self._engine
                if engine is None:
                    from app.audio import get_default_engine

                    engine = get_default_engine()
                engine.play_variation(FIGHT_SOUND, timestamp=timestamp)

        self._elapsed = current.elapsed if current is not None else 0.0

    def draw(
        self,
        surface: pygame.Surface,
        labels: tuple[str, str],
        hud: Hud | None = None,
        ball_positions: tuple[Vec2, Vec2] | None = None,
    ) -> None:  # pragma: no cover - visual
        """Render the intro on ``surface`` using the configured renderer."""
        if self._state is IntroState.DONE:
            # Preserve the final frame of the intro sequence by skipping any
            # further rendering once all animations have completed. This
            # mirrors ``animation-fill-mode: forwards`` in CSS where the last
            # frame remains visible instead of resetting to the initial state.
            return

        progress = self._progress()
        if self._state is IntroState.FADE_OUT and self._targets is None:
            if hud is None:
                hud = Hud(settings.theme)
            label_a, label_b, logo_rect, _ = hud.compute_layout(surface, labels)
            self._targets = (logo_rect, label_a, label_b)
        self._renderer.draw(
            surface,
            labels,
            progress,
            self._state,
            self._targets,
            ball_positions,
            self._elapsed,
        )

    def is_finished(self) -> bool:
        """Return ``True`` if the intro has completed."""

        return self._state is IntroState.DONE

    # internal helpers -----------------------------------------------------
    def _state_progress(self) -> float:
        timeline = self._timeline
        current = timeline.current if timeline is not None else None
        if current is None:
            return 1.0
        return current.progress

    def _progress(self) -> float:
        t = self._state_progress()
        if self._state is IntroState.LOGO_IN:
            return self.config.micro_bounce(t)
        if self._state is IntroState.WEAPONS_IN:
            return 1.0 + self.config.pulse(t) * WEAPON_PULSE_AMPLITUDE
        if self._state is IntroState.HOLD:
            return 1.0
        if self._state is IntroState.FADE_OUT:
            return 1.0 - self.config.fade(t)
        if self._state is IntroState.DONE:
            return 0.0
        return 0.0
