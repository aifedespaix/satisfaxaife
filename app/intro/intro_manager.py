from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pygame

from app.core.config import settings
from app.core.utils import clamp
from app.render.hud import Hud
from app.render.intro_renderer import IntroRenderer

from .assets import IntroAssets
from .config import IntroConfig

if TYPE_CHECKING:  # pragma: no cover - hints only
    import pygame

    from app.audio import AudioEngine


FIGHT_SOUND: str = "assets/fight.ogg"


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
        self._elapsed = 0.0
        self._targets: tuple[pygame.Rect, pygame.Rect, pygame.Rect] | None = None

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

        if self.config.allow_skip and events:
            import pygame

            for event in events:
                if (
                    getattr(event, "type", None) == pygame.KEYDOWN
                    and getattr(event, "key", None) == self.config.skip_key
                ):
                    self._state = IntroState.DONE
                    return

        self._elapsed += dt
        if self._elapsed >= self._current_duration():
            self._advance_state()

    def draw(
        self, surface: pygame.Surface, labels: tuple[str, str], hud: Hud
    ) -> None:  # pragma: no cover - visual
        """Render the intro on ``surface`` using the configured renderer."""

        progress = self._progress()
        if self._state is IntroState.FADE_OUT and self._targets is None:
            self._targets = hud.compute_layout(surface, labels)
        self._renderer.draw(surface, labels, progress, self._state, self._targets)

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
        next_state = {
            IntroState.LOGO_IN: IntroState.WEAPONS_IN,
            IntroState.WEAPONS_IN: IntroState.HOLD,
            IntroState.HOLD: IntroState.FADE_OUT,
            IntroState.FADE_OUT: IntroState.DONE,
        }.get(self._state, IntroState.DONE)
        if self._state is IntroState.HOLD and next_state is IntroState.FADE_OUT:
            timestamp = self.config.logo_in + self.config.weapons_in + self.config.hold
            engine = self._engine
            if engine is None:
                from app.audio import get_default_engine

                engine = get_default_engine()
            engine.play_variation(FIGHT_SOUND, timestamp=timestamp)
        self._elapsed = 0.0
        self._state = next_state

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
