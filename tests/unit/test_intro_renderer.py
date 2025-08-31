from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

pygame = pytest.importorskip("pygame")

if TYPE_CHECKING:  # pragma: no cover - type hints only
    import pygame as _pygame

from app.intro import IntroConfig, IntroState  # noqa: E402
from app.render.intro_renderer import IntroRenderer  # noqa: E402


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


def test_compute_alpha_in_states_monotonic() -> None:
    renderer = IntroRenderer(200, 100)
    progresses = [0.0, 0.3, 0.6, 1.0]
    for state in (IntroState.LOGO_IN, IntroState.WEAPONS_IN):
        alphas = [renderer.compute_alpha(p, state) for p in progresses]
        assert alphas[0] == 0
        assert alphas[-1] == 255
        assert all(a0 <= a1 for a0, a1 in zip(alphas, alphas[1:], strict=False))


def test_compute_alpha_fade_out() -> None:
    renderer = IntroRenderer(200, 100)
    progresses = [1.0, 0.75, 0.5, 0.25, 0.0]
    alphas = [renderer.compute_alpha(p, IntroState.FADE_OUT) for p in progresses]
    assert alphas[0] == 255
    assert alphas[-1] == 0
    assert all(a0 >= a1 for a0, a1 in zip(alphas, alphas[1:], strict=False))


def test_compute_alpha_custom_fade() -> None:
    config = IntroConfig(fade=lambda t: t)
    renderer = IntroRenderer(200, 100, config=config)
    assert renderer.compute_alpha(0.25, IntroState.LOGO_IN) == int(0.25 * 255)


def test_draw_glow_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    pygame.init()
    renderer = IntroRenderer(200, 100)
    surface = pygame.Surface((200, 100), flags=pygame.SRCALPHA)
    blits: list[tuple[int, int]] = []

    original_blit = pygame.Surface.blit

    def counting_blit(
        self: _pygame.Surface,
        source: _pygame.Surface,
        dest: _pygame.Rect | tuple[int, int],
        *args: object,
        **kwargs: object,
    ) -> _pygame.Rect:
        center = dest.center if hasattr(dest, "center") else dest
        blits.append(center)
        return original_blit(self, source, dest, *args, **kwargs)

    monkeypatch.setattr(pygame.Surface, "blit", counting_blit)

    renderer.draw(surface, ("A", "B"), 1.0, IntroState.HOLD)

    left, right, center = renderer.compute_positions(1.0)
    expected_centers: list[tuple[int, int]] = []
    for base in (left, right, center):
        bx, by = int(base[0]), int(base[1])
        expected_centers.extend(
            [
                (bx + 4, by + 4),
                (bx - 2, by),
                (bx + 2, by),
                (bx, by - 2),
                (bx, by + 2),
                (bx, by),
            ]
        )

    assert len(blits) == len(expected_centers)
    assert set(expected_centers).issubset(set(blits))
