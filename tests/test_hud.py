from __future__ import annotations

import pygame
import pytest

from app.core.config import settings
from app.render.hud import Hud
from app.render.renderer import Renderer


def test_hud_draws_without_errors() -> None:
    renderer = Renderer(100, 200)
    hud = Hud(settings.theme)
    renderer.clear()
    hud.draw_title(renderer.surface, "Test")
    hud.draw_hp_bars(renderer.surface, 0.5, 0.5, ("A", "B"))
    hud.draw_watermark(renderer.surface, settings.hud.watermark)
    renderer.present()
    frame = renderer.capture_frame()
    assert frame.shape == (200, 100, 3)


def test_hp_bar_background_color() -> None:
    renderer = Renderer(800, 300)
    hud = Hud(settings.theme)
    renderer.clear()
    for _ in range(25):
        hud.draw_hp_bars(renderer.surface, 0.5, 0.25, ("A", "B"))
    empty = settings.theme.hp_empty
    bar_width = int(renderer.surface.get_width() * Hud.BAR_WIDTH_RATIO)
    bar_height = int(renderer.surface.get_height() * Hud.BAR_HEIGHT_RATIO)
    y = 120 + bar_height // 2
    width_a = int(bar_width * hud.current_hp_a)
    left_empty_x = 40 + width_a + 1
    assert renderer.surface.get_at((left_empty_x, y))[:3] == empty
    right_rect_start = renderer.surface.get_width() - 40 - bar_width
    assert renderer.surface.get_at((right_rect_start + 1, y))[:3] == empty


def test_hp_bar_low_hp_color() -> None:
    renderer = Renderer(800, 300)
    hud = Hud(settings.theme)
    renderer.clear()
    for _ in range(25):
        hud.draw_hp_bars(renderer.surface, 0.2, 0.8, ("A", "B"))
    bar_width = int(renderer.surface.get_width() * Hud.BAR_WIDTH_RATIO)
    bar_height = int(renderer.surface.get_height() * Hud.BAR_HEIGHT_RATIO)
    x = 40 + bar_width // 10
    y = 120 + bar_height // 2
    assert renderer.surface.get_at((x, y))[:3] == settings.theme.hp_warning
    right_x = renderer.surface.get_width() - 40 - bar_width + bar_width // 2
    assert renderer.surface.get_at((right_x, y))[:3] != settings.theme.hp_warning


def test_hp_bars_scale_with_surface(monkeypatch: pytest.MonkeyPatch) -> None:
    hud = Hud(settings.theme)

    small_surface = pygame.Surface((400, 300))
    large_surface = pygame.Surface((800, 600))

    captured_small: list[pygame.Rect] = []
    captured_large: list[pygame.Rect] = []

    def capture_small(
        surface: pygame.Surface, color: pygame.Color | tuple[int, int, int], rect: pygame.Rect
    ) -> pygame.Rect:
        captured_small.append(rect.copy())
        return rect

    def capture_large(
        surface: pygame.Surface, color: pygame.Color | tuple[int, int, int], rect: pygame.Rect
    ) -> pygame.Rect:
        captured_large.append(rect.copy())
        return rect

    monkeypatch.setattr(pygame.draw, "rect", capture_small)
    hud.draw_hp_bars(small_surface, 1.0, 1.0, ("A", "B"))

    monkeypatch.setattr(pygame.draw, "rect", capture_large)
    hud.draw_hp_bars(large_surface, 1.0, 1.0, ("A", "B"))

    assert captured_small[0].width == int(small_surface.get_width() * Hud.BAR_WIDTH_RATIO)
    assert captured_large[0].width == int(large_surface.get_width() * Hud.BAR_WIDTH_RATIO)
    assert captured_small[0].height == int(small_surface.get_height() * Hud.BAR_HEIGHT_RATIO)
    assert captured_large[0].height == int(large_surface.get_height() * Hud.BAR_HEIGHT_RATIO)


def test_hp_interpolation_converges() -> None:
    hud = Hud(settings.theme)
    for _ in range(25):
        hud.update_hp(0.0, 0.5)
    assert hud.current_hp_a == pytest.approx(0.0, abs=1e-2)
    assert hud.current_hp_b == pytest.approx(0.5, abs=1e-2)


def test_hp_label_and_vs_positions() -> None:
    hud = Hud(settings.theme)
    surface = pygame.Surface((800, 600))
    label_a_rect, label_b_rect, logo_rect, vs_rect = hud.draw_hp_bars(
        surface, 1.0, 1.0, ("Alpha", "Beta")
    )

    bar_width = int(surface.get_width() * Hud.BAR_WIDTH_RATIO)
    bar_height = int(surface.get_height() * Hud.BAR_HEIGHT_RATIO)
    left_rect = pygame.Rect(40, 120, bar_width, bar_height)
    right_rect = pygame.Rect(surface.get_width() - 40 - bar_width, 120, bar_width, bar_height)

    assert label_a_rect.left == left_rect.left + Hud.LABEL_PADDING
    assert label_a_rect.right <= left_rect.right - Hud.LABEL_PADDING
    assert label_b_rect.right == right_rect.right - Hud.LABEL_PADDING
    assert label_b_rect.left >= right_rect.left + Hud.LABEL_PADDING

    assert vs_rect.centerx == surface.get_width() // 2
    assert vs_rect.bottom == left_rect.top - Hud.VS_MARGIN
    assert vs_rect.width == int(surface.get_width() * Hud.VS_WIDTH_RATIO)
    assert logo_rect.centerx == surface.get_width() // 2
    assert logo_rect.bottom == left_rect.top - Hud.LOGO_MARGIN


def test_hp_gradient_static() -> None:
    surface = pygame.Surface((800, 300))
    hud = Hud(settings.theme)
    bar_width = int(surface.get_width() * Hud.BAR_WIDTH_RATIO)
    bar_height = int(surface.get_height() * Hud.BAR_HEIGHT_RATIO)
    x = 40 + bar_width // 4
    y = 120 + bar_height // 2

    hud.draw_hp_bars(surface, 1.0, 1.0, ("A", "B"))
    color1 = surface.get_at((x, y))[:3]

    surface.fill((0, 0, 0))
    hud.draw_hp_bars(surface, 1.0, 1.0, ("A", "B"))
    color2 = surface.get_at((x, y))[:3]

    assert color1 == color2


def test_hp_gradient_diagonal_orientation() -> None:
    surface = pygame.Surface((400, 200))
    hud = Hud(settings.theme)
    hud.draw_hp_bars(surface, 1.0, 1.0, ("A", "B"))

    bar_width = int(surface.get_width() * Hud.BAR_WIDTH_RATIO)
    bar_height = int(surface.get_height() * Hud.BAR_HEIGHT_RATIO)
    left_rect = pygame.Rect(40, 120, bar_width, bar_height)

    c1 = surface.get_at((left_rect.x + 5, left_rect.y + 10))[:3]
    c2 = surface.get_at((left_rect.x + 10, left_rect.y + 5))[:3]
    assert c1 == c2
