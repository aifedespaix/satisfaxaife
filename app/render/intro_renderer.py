from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.types import Vec2

if TYPE_CHECKING:  # pragma: no cover - hints only
    import pygame


class IntroRenderer:
    """Render the pre-match introduction with slide and fade effects."""

    def __init__(self, width: int, height: int, font: pygame.font.Font | None = None) -> None:
        self.width = width
        self.height = height
        self.font: pygame.font.Font | None = font

    def compute_positions(self, progress: float) -> tuple[Vec2, Vec2, Vec2]:
        """Compute positions for the two labels and the central marker.

        Parameters
        ----------
        progress:
            Animation progress in ``[0, 1]``.

        Returns
        -------
        tuple[Vec2, Vec2, Vec2]
            Coordinates for the left label, right label and center marker.
        """
        p = max(0.0, min(1.0, progress))
        offset = (1.0 - p) * self.width * 0.5
        left = (self.width * 0.25 - offset, self.height * 0.5)
        right = (self.width * 0.75 + offset, self.height * 0.5)
        center = (self.width * 0.5, self.height * 0.5)
        return left, right, center

    def compute_alpha(self, progress: float) -> int:
        """Return the opacity value for ``progress``.

        The alpha ramps from transparent to opaque over the first half of the
        animation and back to transparent during the second half.
        """
        p = max(0.0, min(1.0, progress))
        if p <= 0.5:
            return int(p / 0.5 * 255)
        return int((1.0 - (p - 0.5) / 0.5) * 255)

    def draw(self, surface: pygame.Surface, labels: tuple[str, str], progress: float) -> None:
        """Render the intro text to ``surface``.

        Parameters
        ----------
        surface:
            Destination surface where elements are drawn.
        labels:
            Names to display on the left and right.
        progress:
            Animation progress in ``[0, 1]``.
        """
        import pygame

        if self.font is None:
            pygame.font.init()
            self.font = pygame.font.Font(None, 72)

        left_pos, right_pos, center_pos = self.compute_positions(progress)
        alpha = self.compute_alpha(progress)

        left_text = self.font.render(labels[0], True, (255, 255, 255))
        right_text = self.font.render(labels[1], True, (255, 255, 255))
        vs_text = self.font.render("VS", True, (255, 255, 255))

        left_text.set_alpha(alpha)
        right_text.set_alpha(alpha)
        vs_text.set_alpha(alpha)

        surface.blit(left_text, left_text.get_rect(center=left_pos))
        surface.blit(right_text, right_text.get_rect(center=right_pos))
        surface.blit(vs_text, vs_text.get_rect(center=center_pos))
