from __future__ import annotations

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
    hud.draw_hp_bars(renderer.surface, 0.5, 0.25, ("A", "B"))
    empty = settings.theme.hp_empty
    y = 120 + 25 // 2
    left_empty_x = 40 + int(300 * 0.5) + 1
    assert renderer.surface.get_at((left_empty_x, y))[:3] == empty
    right_rect_start = renderer.surface.get_width() - 40 - 300
    assert renderer.surface.get_at((right_rect_start + 1, y))[:3] == empty
