from __future__ import annotations

from app.render.hud import Hud
from app.render.renderer import Renderer


def test_hud_draws_without_errors() -> None:
    renderer = Renderer(100, 200)
    hud = Hud()
    renderer.clear()
    hud.draw_title(renderer.surface, "Test")
    hud.draw_hp_bars(renderer.surface, 0.5, 0.5, ("A", "B"))
    hud.draw_watermark(renderer.surface)
    renderer.present()
    frame = renderer.capture_frame()
    assert frame.shape == (200, 100, 3)
