from __future__ import annotations

from app.core.config import settings
from app.render.hud import Hud
from app.render.intro_renderer import IntroRenderer
from app.render.renderer import Renderer


class IntroManager:
    """Manage the pre-match introduction sequence."""

    def __init__(self, intro_renderer: IntroRenderer | None = None) -> None:
        self._renderer = intro_renderer or IntroRenderer(settings.width, settings.height)

    def play(self, renderer: Renderer, hud: Hud) -> None:
        """Render the intro. Currently this is a no-op."""
        _ = renderer, hud

    def draw(self, renderer: Renderer, labels: tuple[str, str], progress: float) -> None:
        """Delegate rendering to :class:`IntroRenderer`.

        Parameters
        ----------
        renderer:
            Main renderer used for the match.
        labels:
            Names of the opposing sides.
        progress:
            Animation progress in ``[0, 1]``.
        """
        self._renderer.draw(renderer.surface, labels, progress)
