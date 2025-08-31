from __future__ import annotations

from app.render.hud import Hud
from app.render.renderer import Renderer


class IntroManager:
    """Manage the pre-match introduction sequence."""

    def play(self, renderer: Renderer, hud: Hud) -> None:
        """Render the intro. Currently this is a no-op."""
        # Future implementations may animate logos or countdowns here.
        _ = renderer, hud
