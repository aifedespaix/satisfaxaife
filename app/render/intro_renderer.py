from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from app.core.types import Vec2
from app.core.utils import clamp

if TYPE_CHECKING:  # pragma: no cover - hints only
    from app.intro.assets import IntroAssets
    from app.intro.config import IntroConfig
    from app.intro.intro_manager import IntroState


class IntroRenderer:
    """Render the pre-match introduction with slide, glow and fade effects."""

    WEAPON_WIDTH_RATIO: float = 0.4
    IMAGE_TEXT_GAP: float = 10.0

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

    def _interpolate_to_targets(
        self,
        elements: list[tuple[pygame.Surface, Vec2]],
        start_positions: tuple[Vec2, Vec2, Vec2],
        targets: tuple[pygame.Rect, pygame.Rect, pygame.Rect],
        progress: float,
    ) -> None:
        """Mutate elements to move and scale toward their target rectangles.

        The last three entries of ``elements`` are expected to be the logo, the
        left label and the right label in that order. ``start_positions`` and
        ``targets`` must follow the same ordering.
        """

        q = clamp(1.0 - progress, 0.0, 1.0)
        start_index = len(elements) - 3
        for i, idx in enumerate(range(start_index, len(elements))):
            img, _ = elements[idx]
            start = start_positions[i]
            target = targets[i]
            new_pos = (
                start[0] + (target.centerx - start[0]) * q,
                start[1] + (target.centery - start[1]) * q,
            )
            sw, sh = img.get_size()
            new_w = max(1, int(sw + (target.width - sw) * q))
            new_h = max(1, int(sh + (target.height - sh) * q))
            img = pygame.transform.smoothscale(img, (new_w, new_h))
            elements[idx] = (img, new_pos)

    def _equip_weapons(
        self,
        elements: list[tuple[pygame.Surface, Vec2]],
        ball_positions: tuple[Vec2, Vec2],
        progress: float,
    ) -> None:
        """Move weapon sprites toward ``ball_positions`` and shrink them."""

        q = clamp(1.0 - progress, 0.0, 1.0)
        for i in range(2):
            img, start = elements[i]
            target = ball_positions[i]
            new_pos = (
                start[0] + (target[0] - start[0]) * q,
                start[1] + (target[1] - start[1]) * q,
            )
            sw, sh = img.get_size()
            new_w = max(1, int(sw * (1.0 - q)))
            new_h = max(1, int(sh * (1.0 - q)))
            img = pygame.transform.smoothscale(img, (new_w, new_h))
            elements[i] = (img, new_pos)

    def _prepare_elements(
        self,
        labels: tuple[str, str],
        progress: float,
        left_pos: Vec2,
        right_pos: Vec2,
        center_pos: Vec2,
    ) -> list[tuple[pygame.Surface, Vec2]]:
        """Return surfaces and positions for rendering."""
        if self.assets is not None:
            if self.font is None:
                self.font = self.assets.font
            text_surfaces = [
                (self.font.render(labels[0], True, (255, 255, 255)), left_pos),
                (self.font.render(labels[1], True, (255, 255, 255)), right_pos),
            ]
            weapon_surfaces: list[tuple[pygame.Surface, Vec2]] = []
            for source, (text_surf, pos) in zip(
                (self.assets.weapon_a, self.assets.weapon_b), text_surfaces, strict=False
            ):
                target_width = self.width * self.WEAPON_WIDTH_RATIO
                scale = target_width / source.get_width()
                img = pygame.transform.rotozoom(source, (progress - 0.5) * 10, scale)
                text_height = text_surf.get_height()
                img_y = pos[1] - text_height / 2 - self.IMAGE_TEXT_GAP - img.get_height() / 2
                weapon_surfaces.append((img, (pos[0], img_y)))
            logo_img = pygame.transform.rotozoom(
                self.assets.logo, (progress - 0.5) * 10, self.config.logo_scale
            )
            logo_and_text = [(logo_img, center_pos)] + text_surfaces
            return weapon_surfaces + logo_and_text
        if self.font is None:
            pygame.font.init()
            self.font = pygame.font.Font(None, 72)
        logo = self.font.render("VS", True, (255, 255, 255))
        return [
            (logo, center_pos),
            (self.font.render(labels[0], True, (255, 255, 255)), left_pos),
            (self.font.render(labels[1], True, (255, 255, 255)), right_pos),
        ]

    def draw(
        self,
        surface: pygame.Surface,
        labels: tuple[str, str],
        progress: float,
        state: IntroState,
        targets: tuple[pygame.Rect, pygame.Rect, pygame.Rect] | None = None,
        ball_positions: tuple[Vec2, Vec2] | None = None,
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
        targets:
            Optional rectangles defining target positions and sizes for the
            logo and the two labels. When provided and ``state`` is
            ``FADE_OUT``, elements interpolate toward these rectangles.
        ball_positions:
            Optional target coordinates for the weapon sprites. When provided
            during the ``FADE_OUT`` state, weapon sprites move toward these
            positions while shrinking to simulate equipping.
        """
        from app.intro.intro_manager import IntroState as _IntroState

        if state is _IntroState.FADE_OUT and targets is not None:
            left_pos, right_pos, center_pos = self.compute_positions(1.0)
        else:
            left_pos, right_pos, center_pos = self.compute_positions(progress)
        alpha = self.compute_alpha(progress, state)
        elements = self._prepare_elements(labels, progress, left_pos, right_pos, center_pos)

        if state is _IntroState.FADE_OUT:
            if targets is not None:
                self._interpolate_to_targets(
                    elements,
                    (center_pos, left_pos, right_pos),
                    targets,
                    progress,
                )
            if ball_positions is not None:
                self._equip_weapons(elements, ball_positions, progress)

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

        fade_alpha = 0
        if state is _IntroState.LOGO_IN:
            fade_alpha = int((1.0 - progress) * 255)

        if fade_alpha > 0:
            overlay = pygame.Surface((self.width, self.height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(fade_alpha)
            surface.blit(overlay, (0, 0))
