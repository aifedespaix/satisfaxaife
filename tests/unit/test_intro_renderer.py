from __future__ import annotations

from app.intro import IntroConfig
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


def test_compute_positions_custom_config() -> None:
    config = IntroConfig(
        left_pos_pct=(0.3, 0.4),
        right_pos_pct=(0.7, 0.6),
        center_pos_pct=(0.5, 0.5),
        slide_offset_pct=0.4,
    )
    renderer = IntroRenderer(100, 200, config=config)
    left_end, right_end, center = renderer.compute_positions(1.0)
    assert left_end == (30.0, 80.0)
    assert right_end == (70.0, 120.0)
    assert center == (50.0, 100.0)


def test_compute_alpha_fade_in_out() -> None:
    renderer = IntroRenderer(200, 100)
    assert renderer.compute_alpha(0.0) == 0
    assert renderer.compute_alpha(0.5) == 255
    assert renderer.compute_alpha(1.0) == 0


def test_compute_alpha_custom_fade() -> None:
    config = IntroConfig(fade=lambda t: t)
    renderer = IntroRenderer(200, 100, config=config)
    assert renderer.compute_alpha(0.25) == int(0.5 * 255)
