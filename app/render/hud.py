from __future__ import annotations

import pygame

from app.render.theme import Theme, draw_horizontal_gradient


class Hud:
    """Draw heads-up display elements."""

    def __init__(self, theme: Theme) -> None:
        pygame.font.init()
        self.theme = theme
        self.title_font = pygame.font.Font(None, 72)
        self.bar_font = pygame.font.Font(None, 48)
        self.watermark_font = pygame.font.Font(None, 36)

    def draw_title(self, surface: pygame.Surface, text: str) -> None:
        """Render the main title centered at the top of the screen."""
        title = self.title_font.render(text, True, (255, 255, 255))
        rect = title.get_rect(center=(surface.get_width() // 2, 60))
        surface.blit(title, rect)

    def draw_hp_bars(
        self, surface: pygame.Surface, hp_a: float, hp_b: float, labels: tuple[str, str]
    ) -> None:
        """Draw two symmetrical health bars with labels using theme gradients."""
        bar_width = 300
        bar_height = 25
        margin = 40

        # Left bar (team A)
        left_rect = pygame.Rect(margin, 120, bar_width, bar_height)
        draw_horizontal_gradient(
            surface, left_rect, *self.theme.team_a.hp_gradient
        )
        pygame.draw.rect(
            surface,
            self.theme.team_a.primary,
            (left_rect.x, left_rect.y, int(bar_width * hp_a), bar_height),
        )
        label_a = self.bar_font.render(labels[0], True, (255, 255, 255))
        surface.blit(label_a, (left_rect.x, left_rect.y - 30))

        # Right bar (team B)
        right_rect = pygame.Rect(
            surface.get_width() - margin - bar_width, 120, bar_width, bar_height
        )
        # Gradient drawn right-to-left
        grad_start, grad_end = self.theme.team_b.hp_gradient
        draw_horizontal_gradient(surface, right_rect, grad_end, grad_start)
        pygame.draw.rect(
            surface,
            self.theme.team_b.primary,
            (
                right_rect.x + bar_width - int(bar_width * hp_b),
                right_rect.y,
                int(bar_width * hp_b),
                bar_height,
            ),
        )
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

    def draw_victory_banner(
        self, surface: pygame.Surface, title: str, subtitle: str
    ) -> None:
        """Draw the final victory banner at the center of the screen."""
        title_surf = self.title_font.render(title, True, (255, 255, 255))
        sub_surf = self.bar_font.render(subtitle, True, (255, 255, 255))
        center_x = surface.get_width() // 2
        center_y = surface.get_height() // 2
        title_rect = title_surf.get_rect(center=(center_x, center_y - 30))
        sub_rect = sub_surf.get_rect(center=(center_x, center_y + 20))
        surface.blit(title_surf, title_rect)
        surface.blit(sub_surf, sub_rect)
