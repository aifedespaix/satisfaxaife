from __future__ import annotations

import pytest

pygame = pytest.importorskip("pygame")

from app.intro import IntroState  # noqa: E402
from app.render.intro_renderer import IntroRenderer  # noqa: E402


def test_positions_static_between_hold_and_fade_out(monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.init()
    renderer = IntroRenderer(200, 100)
    surface = pygame.Surface((200, 100), flags=pygame.SRCALPHA)
    labels = ("A", "B")

    positions: list[tuple[tuple[float, float], tuple[float, float], tuple[float, float]]] = []

    original_compute = renderer.compute_positions

    def tracking(
        progress: float,
    ) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float]]:
        pos = original_compute(progress)
        positions.append(pos)
        return pos

    monkeypatch.setattr(renderer, "compute_positions", tracking)

    renderer.draw(surface, labels, 0.0, IntroState.WEAPONS_IN)
    renderer.draw(surface, labels, 0.0, IntroState.HOLD)
    for progress in (1.0, 0.5, 0.0):
        renderer.draw(surface, labels, progress, IntroState.FADE_OUT)

    assert len({pos for pos in positions}) == 1
    pygame.quit()
