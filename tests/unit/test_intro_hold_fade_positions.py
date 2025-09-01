from __future__ import annotations

import pytest

pygame = pytest.importorskip("pygame")

from app.intro import IntroState  # noqa: E402
from app.render.intro_renderer import IntroRenderer  # noqa: E402


def test_positions_static_between_hold_and_fade_out(monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.init()
    renderer = IntroRenderer(200, 100)
    positions: list[tuple[tuple[float, float], tuple[float, float], tuple[float, float]]] = []

    original_compute = renderer.compute_positions

    def tracking(progress: float) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        pos = original_compute(progress)
        positions.append(pos)
        return pos

    monkeypatch.setattr(renderer, "compute_positions", tracking)

    renderer._compute_state_positions(0.0, IntroState.WEAPONS_IN)
    renderer._compute_state_positions(0.0, IntroState.HOLD)
    for progress in (1.0, 0.5, 0.0):
        renderer._compute_state_positions(progress, IntroState.FADE_OUT)

    assert len({pos for pos in positions}) == 1
    pygame.quit()


def test_first_fade_out_frame_matches_last_hold_frame(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pygame.init()
    renderer = IntroRenderer(200, 100)

    # Ensure final positions are cached
    renderer._compute_state_positions(0.0, IntroState.WEAPONS_IN)

    base = pygame.Surface((10, 10), flags=pygame.SRCALPHA)
    elements = [(base, (10.0, 10.0))]
    monkeypatch.setattr(renderer, "_hold_offset", lambda elapsed: 5.0)

    hold_elements, hold_angle = renderer._apply_hold_effect(elements, 0.0, 0.0)

    left, right, center = renderer._compute_state_positions(1.0, IntroState.FADE_OUT)
    fade_elements, fade_angle = renderer._apply_fade_out(
        elements, 0.0, 1.0, None, None, left, right, center
    )

    assert hold_angle == fade_angle
    assert hold_elements[0][1] == fade_elements[0][1]
    pygame.quit()
