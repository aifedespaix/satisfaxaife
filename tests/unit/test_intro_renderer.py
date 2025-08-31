from __future__ import annotations

from app.render.intro_renderer import IntroRenderer


def test_compute_positions_slide_and_center() -> None:
    renderer = IntroRenderer(200, 100)
    left_start, right_start, center = renderer.compute_positions(0.0)
    assert left_start[0] < 0
    assert right_start[0] > renderer.width
    assert center == (100.0, 50.0)

    left_end, right_end, _ = renderer.compute_positions(1.0)
    assert left_end == (50.0, 50.0)
    assert right_end == (150.0, 50.0)


def test_compute_alpha_fade_in_out() -> None:
    renderer = IntroRenderer(200, 100)
    assert renderer.compute_alpha(0.0) == 0
    assert renderer.compute_alpha(0.5) == 255
    assert renderer.compute_alpha(1.0) == 0
