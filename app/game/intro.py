from __future__ import annotations

from app.core.config import settings
from app.intro import IntroState
from app.render.hud import Hud
from app.render.intro_renderer import IntroRenderer
from app.render.renderer import Renderer


class IntroManager:
    """Manage the pre-match introduction sequence."""

    def __init__(
        self,
        labels: tuple[str, str] = ("", ""),
        intro_renderer: IntroRenderer | None = None,
        *,
        duration: float = 1.0,
    ) -> None:
        self._renderer = intro_renderer or IntroRenderer(settings.width, settings.height)
        self._labels = labels
        self._duration = duration
        self._elapsed = 0.0
        self._skipped = False

    def is_finished(self) -> bool:
        """Return ``True`` when the intro has completed or was skipped."""

        return self._skipped or self._elapsed >= self._duration

    def skip(self) -> None:
        """Terminate the intro prematurely."""

        self._skipped = True

    def update(self, dt: float) -> None:
        """Advance the intro state by ``dt`` seconds."""

        if not self.is_finished():
            self._elapsed += dt

    def draw(self, renderer: Renderer, hud: Hud) -> None:
        """Render the current frame of the intro sequence."""

        progress = 1.0 if self._duration == 0 else min(self._elapsed / self._duration, 1.0)
        self._renderer.draw(renderer.surface, self._labels, progress, IntroState.LOGO_IN)
        hud.draw_title(renderer.surface, settings.hud.title)
        hud.draw_watermark(renderer.surface, settings.hud.watermark)
