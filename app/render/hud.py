from __future__ import annotations

import pygame

from app.render.theme import Theme, draw_horizontal_gradient


class Hud:
    """Draw heads-up display elements."""

    BAR_WIDTH_RATIO: float = 0.45
    BAR_HEIGHT_RATIO: float = 0.03
    HP_INTERPOLATION_RATE: float = 0.2

    def __init__(self, theme: Theme) -> None:
        pygame.font.init()
        self.theme = theme
        self.title_font = pygame.font.Font(None, 72)
        self.bar_font = pygame.font.Font(None, 48)
        self.watermark_font = pygame.font.Font(None, 36)
        self.current_hp_a = 1.0
        self.current_hp_b = 1.0

    def update_hp(self, hp_a: float, hp_b: float) -> None:
        """Interpolate the displayed health toward the target values.

        Parameters
        ----------
        hp_a: float
            Target health ratio for team A in ``[0, 1]``.
        hp_b: float
            Target health ratio for team B in ``[0, 1]``.
        """

        hp_a = max(0.0, min(1.0, hp_a))
        hp_b = max(0.0, min(1.0, hp_b))
        self.current_hp_a += (hp_a - self.current_hp_a) * self.HP_INTERPOLATION_RATE
        self.current_hp_b += (hp_b - self.current_hp_b) * self.HP_INTERPOLATION_RATE

    def draw_title(self, surface: pygame.Surface, text: str) -> None:
        """Render the main title centered at the top of the screen."""
        title = self.title_font.render(text, True, (255, 255, 255))
        rect = title.get_rect(center=(surface.get_width() // 2, 60))
        surface.blit(title, rect)

    def draw_hp_bars(
        self, surface: pygame.Surface, hp_a: float, hp_b: float, labels: tuple[str, str]
    ) -> None:
        """Draw two symmetrical health bars with labels.

        The bar dimensions scale with the given surface so that the HUD adapts
        to different resolutions.
        """

        bar_width = max(1, int(surface.get_width() * self.BAR_WIDTH_RATIO))
        bar_height = max(1, int(surface.get_height() * self.BAR_HEIGHT_RATIO))
        margin = 40

        self.update_hp(hp_a, hp_b)

        # Left bar (team A)
        left_rect = pygame.Rect(margin, 120, bar_width, bar_height)
        pygame.draw.rect(surface, self.theme.hp_empty, left_rect)
        width_a = int(bar_width * self.current_hp_a)
        if width_a > 0:
            filled_rect = pygame.Rect(left_rect.x, left_rect.y, width_a, bar_height)
            draw_horizontal_gradient(surface, filled_rect, *self.theme.team_a.hp_gradient)
        label_a = self.bar_font.render(labels[0], True, (255, 255, 255))
        surface.blit(label_a, (left_rect.x, left_rect.y - 30))

        # Right bar (team B)
        right_rect = pygame.Rect(
            surface.get_width() - margin - bar_width, 120, bar_width, bar_height
        )
        pygame.draw.rect(surface, self.theme.hp_empty, right_rect)
        width_b = int(bar_width * self.current_hp_b)
        if width_b > 0:
            filled_rect = pygame.Rect(
                right_rect.x + bar_width - width_b, right_rect.y, width_b, bar_height
            )
            grad_start, grad_end = self.theme.team_b.hp_gradient
            draw_horizontal_gradient(surface, filled_rect, grad_end, grad_start)
        label_b = self.bar_font.render(labels[1], True, (255, 255, 255))
        surface.blit(
            label_b,
            (right_rect.x + bar_width - label_b.get_width(), right_rect.y - 30),
        )

    def draw_watermark(self, surface: pygame.Surface, text: str) -> None:
        """Draw a small watermark at the bottom-left corner."""
        mark = self.watermark_font.render(text, True, (255, 255, 255))
        rect = mark.get_rect()
        rect.bottomleft = (10, surface.get_height() - 10)
        surface.blit(mark, rect)

    def draw_victory_banner(self, surface: pygame.Surface, title: str, subtitle: str) -> None:
        """Draw the final victory banner at the center of the screen."""
        title_surf = self.title_font.render(title, True, (255, 255, 255))
        sub_surf = self.bar_font.render(subtitle, True, (255, 255, 255))
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2
        title_rect = title_surf.get_rect(center=(center_x, center_y - 30))
        sub_rect = sub_surf.get_rect(center=(center_x, center_y + 20))
        surface.blit(title_surf, title_rect)
        surface.blit(sub_surf, sub_rect)
