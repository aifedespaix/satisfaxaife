from __future__ import annotations

import pygame

from app.render.sprites import ASSET_DIR, load_sprite
from app.render.theme import Theme, draw_diagonal_gradient


class Hud:
    """Draw heads-up display elements."""

    BAR_WIDTH_RATIO: float = 0.45
    BAR_HEIGHT_RATIO: float = 0.03
    HP_INTERPOLATION_RATE: float = 0.2
    LOW_HP_THRESHOLD: float = 0.3
    LABEL_PADDING: int = 10
    VS_WIDTH_RATIO: float = 0.2
    VS_MARGIN: int = -100

    def __init__(self, theme: Theme) -> None:
        """Initialize the HUD renderer.

        Parameters
        ----------
        theme:
            Color palette used for rendering.
        """

        pygame.font.init()
        self.theme = theme
        self.title_font = pygame.font.Font(None, 72)
        weapon_font_path = (ASSET_DIR / "fonts" / "FightKickDemoRegular.ttf").as_posix()
        self.bar_font = pygame.font.Font(weapon_font_path, 48)
        self.watermark_font = pygame.font.Font(None, 36)
        self.current_hp_a = 1.0
        self.current_hp_b = 1.0
        self.vs_image: pygame.Surface = load_sprite("vs.png")

    def compute_layout(
        self, surface: pygame.Surface, labels: tuple[str, str]
    ) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
        """Return target rectangles for the labels and ``VS`` marker.

        Parameters
        ----------
        surface:
            Surface used to determine available size.
        labels:
            Names displayed on the left and right health bars.

        Returns
        -------
        tuple[pygame.Rect, pygame.Rect, pygame.Rect]
            Rectangles of the two labels and the ``VS`` marker positioned as
            they would appear when drawn.
        """

        bar_width = max(1, int(surface.get_width() * self.BAR_WIDTH_RATIO))
        bar_height = max(1, int(surface.get_height() * self.BAR_HEIGHT_RATIO))
        margin = 40

        left_rect = pygame.Rect(margin, 120, bar_width, bar_height)
        right_rect = pygame.Rect(
            surface.get_width() - margin - bar_width, 120, bar_width, bar_height
        )

        label_a = self.bar_font.render(labels[0], True, (255, 255, 255))
        label_a_rect = label_a.get_rect()
        label_a_rect.centery = left_rect.centery
        label_a_rect.left = left_rect.left + self.LABEL_PADDING
        max_left = left_rect.right - self.LABEL_PADDING - label_a_rect.width
        if label_a_rect.left > max_left:
            label_a_rect.left = max_left

        label_b = self.bar_font.render(labels[1], True, (255, 255, 255))
        label_b_rect = label_b.get_rect()
        label_b_rect.centery = right_rect.centery
        label_b_rect.right = right_rect.right - self.LABEL_PADDING
        min_right = right_rect.left + self.LABEL_PADDING + label_b_rect.width
        if label_b_rect.right < min_right:
            label_b_rect.right = min_right

        target_width = max(1, int(surface.get_width() * self.VS_WIDTH_RATIO))
        width, height = self.vs_image.get_size()
        scale = target_width / width
        vs_rect = pygame.Rect(0, 0, target_width, int(height * scale))
        vs_rect.midbottom = (surface.get_width() // 2, left_rect.top - self.VS_MARGIN)

        return label_a_rect, label_b_rect, vs_rect

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
        if not text:
            return
        title = self.title_font.render(text, True, (255, 255, 255))
        rect = title.get_rect(center=(surface.get_width() // 2, 60))
        surface.blit(title, rect)

    def draw_vs(self, surface: pygame.Surface, bar_top: int) -> pygame.Rect:
        """Draw a centered ``VS`` image above the health bars.

        Parameters
        ----------
        surface:
            Surface to draw on.
        bar_top:
            Vertical position of the top of the health bars.

        Returns
        -------
        pygame.Rect
            Rectangle where the marker was rendered.
        """

        target_width = max(1, int(surface.get_width() * self.VS_WIDTH_RATIO))
        width, height = self.vs_image.get_size()
        scale = target_width / width
        scaled = pygame.transform.smoothscale(self.vs_image, (target_width, int(height * scale)))
        rect = scaled.get_rect()
        rect.midbottom = (surface.get_width() // 2, bar_top - self.VS_MARGIN)
        surface.blit(scaled, rect)
        return rect

    def draw_hp_bars(
        self, surface: pygame.Surface, hp_a: float, hp_b: float, labels: tuple[str, str]
    ) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
        """Draw two symmetrical health bars with labels.

        The bar dimensions scale with the given surface so that the HUD adapts
        to different resolutions. A static 45° gradient fills the bars from the
        top-left to the bottom-right corner.

        Returns
        -------
        tuple[pygame.Rect, pygame.Rect, pygame.Rect]
            Rectangles of the two label texts and the ``VS`` marker.
        """

        bar_width = max(1, int(surface.get_width() * self.BAR_WIDTH_RATIO))
        bar_height = max(1, int(surface.get_height() * self.BAR_HEIGHT_RATIO))
        margin = 40

        self.update_hp(hp_a, hp_b)

        layout_a, layout_b, vs_rect = self.compute_layout(surface, labels)

        # Left bar (team A)
        left_rect = pygame.Rect(margin, 120, bar_width, bar_height)
        pygame.draw.rect(surface, self.theme.hp_empty, left_rect)
        width_a = int(bar_width * self.current_hp_a)
        if width_a > 0:
            filled_rect = pygame.Rect(left_rect.x, left_rect.y, width_a, bar_height)
            colors_a = (
                (self.theme.hp_warning,)
                if self.current_hp_a < self.LOW_HP_THRESHOLD
                else self.theme.team_a.hp_gradient
            )
            draw_diagonal_gradient(surface, filled_rect, colors_a)
        label_a = self.bar_font.render(labels[0], True, (255, 255, 255))
        surface.blit(label_a, layout_a)

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
            colors_b = (
                (self.theme.hp_warning,)
                if self.current_hp_b < self.LOW_HP_THRESHOLD
                else tuple(reversed(self.theme.team_b.hp_gradient))
            )
            draw_diagonal_gradient(surface, filled_rect, colors_b)
        label_b = self.bar_font.render(labels[1], True, (255, 255, 255))
        surface.blit(label_b, layout_b)

        scaled_vs = pygame.transform.smoothscale(self.vs_image, vs_rect.size)
        surface.blit(scaled_vs, vs_rect)

        return layout_a, layout_b, vs_rect

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
