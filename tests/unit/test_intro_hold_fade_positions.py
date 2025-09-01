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


def test_first_fade_out_frame_matches_last_hold_frame(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pygame.init()
    renderer = IntroRenderer(200, 100)
    surface = pygame.Surface((200, 100), flags=pygame.SRCALPHA)
    labels = ("A", "B")

    # Ensure final positions are cached
    renderer.draw(surface, labels, 0.0, IntroState.WEAPONS_IN)

    # Prepare deterministic elements and offsets
    base = pygame.Surface((10, 10), flags=pygame.SRCALPHA)
    monkeypatch.setattr(
        renderer,
        "_prepare_elements",
        lambda labels, progress, lp, rp, cp: [(base, (10.0, 10.0))],
    )
    monkeypatch.setattr(renderer, "_compute_transform", lambda progress: (0.0, 1.0))
    monkeypatch.setattr(renderer, "_hold_offset", lambda elapsed: 5.0)

    angles: list[float] = []
    monkeypatch.setattr(
        pygame.transform,
        "rotozoom",
        lambda surf, angle, scale: angles.append(angle) or surf,
    )

    blits: list[tuple[int, int]] = []

    def fake_blit(self: pygame.Surface, src: pygame.Surface, dest, *args, **kwargs):
        rect = dest if isinstance(dest, pygame.Rect) else pygame.Rect(dest, src.get_size())
        blits.append(rect.center)
        return rect

    monkeypatch.setattr(pygame.Surface, "blit", fake_blit, raising=False)

    renderer.draw(surface, labels, 0.0, IntroState.HOLD, elapsed=0.0)
    hold_angle = angles[-1]
    hold_pos = blits[-1]

    angles.clear()
    blits.clear()
    renderer.draw(surface, labels, 1.0, IntroState.FADE_OUT)
    fade_angle = angles[-1]
    fade_pos = blits[-1]

    assert fade_angle == hold_angle
    assert fade_pos == hold_pos
    pygame.quit()
