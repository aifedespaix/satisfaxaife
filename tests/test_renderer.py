from __future__ import annotations

from app.render.renderer import Renderer


def test_capture_frame_shape() -> None:
    renderer = Renderer(100, 200)
    renderer.clear()
    renderer.draw_ball((50.0, 100.0), 10, (255, 255, 255), (255, 0, 0))
    renderer.draw_eyes((50.0, 100.0), (1.0, 0.0), 10, (255, 0, 0))
    renderer.present()
    frame = renderer.capture_frame()
    assert frame.shape == (200, 100, 3)
    assert frame.sum() > 0
