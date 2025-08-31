from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.types import Vec2
from app.core.utils import clamp

if TYPE_CHECKING:  # pragma: no cover - hints only
    import pygame

    from app.intro.assets import IntroAssets
    from app.intro.config import IntroConfig
    from app.intro.intro_manager import IntroState


class IntroRenderer:
    """Render the pre-match introduction with slide, glow and fade effects."""

    def __init__(
        self,
        width: int,
        height: int,
        config: IntroConfig | None = None,
        font: pygame.font.Font | None = None,
        assets: IntroAssets | None = None,
    ) -> None:
        from app.intro.config import IntroConfig as _IntroConfig

        self.width = width
        self.height = height
        self.config = config or _IntroConfig()
        self.font: pygame.font.Font | None = font or (assets.font if assets else None)
        self.assets = assets

    def compute_positions(self, progress: float) -> tuple[Vec2, Vec2, Vec2]:
        """Return positions for the two labels and the central marker.

        Parameters
        ----------
        progress:
            Animation progress in ``[0, 1]`` used to interpolate the slide-in
            effect.

        Returns
        -------
        tuple[Vec2, Vec2, Vec2]
            Pixel coordinates for the left label, right label and centre marker.
        """
        p = clamp(progress, 0.0, 1.0)
        offset = (1.0 - p) * self.width * self.config.slide_offset_pct
        left = (
            self.width * self.config.left_pos_pct[0] - offset,
            self.height * self.config.left_pos_pct[1],
        )
        right = (
            self.width * self.config.right_pos_pct[0] + offset,
            self.height * self.config.right_pos_pct[1],
        )
        center = (
            self.width * self.config.center_pos_pct[0],
            self.height * self.config.center_pos_pct[1],
        )
        return left, right, center

    def compute_alpha(self, progress: float, state: IntroState) -> int:
        """Return opacity for ``progress`` given the intro ``state``.

        ``LOGO_IN`` fades from transparent to fully opaque using the easing
        function from :class:`IntroConfig`. ``WEAPONS_IN`` remains fully opaque
        regardless of progress. ``FADE_OUT`` transitions from opaque to
        transparent. Other states remain fully opaque.
        """
        from app.intro.intro_manager import IntroState as _IntroState

        p = clamp(progress, 0.0, 1.0)
        if state is _IntroState.LOGO_IN:
            return int(self.config.fade(p) * 255)
        if state is _IntroState.WEAPONS_IN:
            return 255
        if state is _IntroState.FADE_OUT:
            return int(p * 255)
        return 255

    def draw(
        self,
        surface: pygame.Surface,
        labels: tuple[str, str],
        progress: float,
        state: IntroState,
    ) -> None:  # pragma: no cover - visual
        """Render the intro text and apply visual effects.

        Parameters
        ----------
        surface:
            Destination surface where elements are drawn.
        labels:
            Names to display on the left and right.
        progress:
            Animation progress in ``[0, 1]``.
        state:
            Current :class:`~app.intro.intro_manager.IntroState` controlling the
            fade behaviour.
        """
        import pygame

        left_pos, right_pos, center_pos = self.compute_positions(progress)
        alpha = self.compute_alpha(progress, state)

        if self.assets is not None:
            surfaces = [
                (self.assets.weapon_a, left_pos, self.config.weapon_scale),
                (self.assets.weapon_b, right_pos, self.config.weapon_scale),
                (self.assets.logo, center_pos, self.config.logo_scale),
            ]
            elements = []
            for source, pos, scale in surfaces:
                img = pygame.transform.rotozoom(source, (progress - 0.5) * 10, scale)
                elements.append((img, pos))
        else:
            if self.font is None:
                pygame.font.init()
                self.font = pygame.font.Font(None, 72)
            elements = [
                (self.font.render(labels[0], True, (255, 255, 255)), left_pos),
                (self.font.render(labels[1], True, (255, 255, 255)), right_pos),
                (self.font.render("VS", True, (255, 255, 255)), center_pos),
            ]

        for img, pos in elements:
            if self.assets is None:
                img = pygame.transform.rotozoom(img, (progress - 0.5) * 10, 1.0)
            img.set_alpha(alpha)
            shadow = img.copy()
            shadow.fill((0, 0, 0, 180), special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(shadow, shadow.get_rect(center=(pos[0] + 4, pos[1] + 4)))
            for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
                glow = img.copy()
                glow.set_alpha(min(alpha, 128))
                surface.blit(glow, glow.get_rect(center=(pos[0] + dx, pos[1] + dy)))
            surface.blit(img, img.get_rect(center=pos))

        fade_alpha = int((1.0 - progress) * 255)
        if fade_alpha > 0:
            overlay = pygame.Surface((self.width, self.height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(fade_alpha)
            surface.blit(overlay, (0, 0))
