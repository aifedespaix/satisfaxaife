from __future__ import annotations

import numpy as np

from app.core.config import settings
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


def test_set_hp_updates_display() -> None:
    renderer = Renderer(100, 200)
    renderer.set_hp(0.25, 0.75)
    assert renderer._hp_display == [0.25, 0.75]


def test_draw_eyes_team_color() -> None:
    renderer = Renderer(100, 100)
    renderer.clear()
    team_color = settings.theme.team_a.primary
    renderer.draw_eyes((50.0, 50.0), (0.0, 0.0), 10, team_color)
    renderer.present()
    frame = renderer.capture_frame()
    assert (frame == np.array(team_color)).all(axis=-1).any()


def test_add_impact_custom_duration() -> None:
    renderer = Renderer(100, 100)
    duration = 0.5
    renderer.add_impact((50.0, 50.0), duration=duration)
    frames = int(duration / settings.dt)
    for _ in range(frames - 1):
        renderer.clear()
    assert len(renderer._impacts) == 1
    renderer.clear()
    assert len(renderer._impacts) == 0
