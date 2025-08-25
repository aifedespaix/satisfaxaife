from __future__ import annotations

import pygame


class Hud:
    """Draw heads-up display elements."""

    def __init__(self) -> None:
        pygame.font.init()
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
        """Draw two symmetrical health bars with labels."""
        bar_width = 300
        bar_height = 25
        margin = 40
        # Left bar
        left_rect = pygame.Rect(margin, 120, bar_width, bar_height)
        pygame.draw.rect(surface, (100, 0, 0), left_rect)
        pygame.draw.rect(
            surface, (200, 0, 0), (left_rect.x, left_rect.y, int(bar_width * hp_a), bar_height)
        )
        label_a = self.bar_font.render(labels[0], True, (255, 255, 255))
        surface.blit(label_a, (left_rect.x, left_rect.y - 30))
        # Right bar
        right_rect = pygame.Rect(
            surface.get_width() - margin - bar_width, 120, bar_width, bar_height
        )
        pygame.draw.rect(surface, (0, 100, 0), right_rect)
        pygame.draw.rect(
            surface,
            (0, 200, 0),
            (
                right_rect.x + bar_width - int(bar_width * hp_b),
                right_rect.y,
                int(bar_width * hp_b),
                bar_height,
            ),
        )
        label_b = self.bar_font.render(labels[1], True, (255, 255, 255))
        surface.blit(label_b, (right_rect.x + bar_width - label_b.get_width(), right_rect.y - 30))

    def draw_watermark(self, surface: pygame.Surface, text: str = "@battleballs") -> None:
        """Draw a small watermark at the bottom-left corner."""
        mark = self.watermark_font.render(text, True, (255, 255, 255))
        rect = mark.get_rect()
        rect.bottomleft = (10, surface.get_height() - 10)
        surface.blit(mark, rect)
