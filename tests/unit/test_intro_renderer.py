from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

pygame = pytest.importorskip("pygame")

if TYPE_CHECKING:  # pragma: no cover - type hints only
    import pygame as _pygame

from app.intro import IntroConfig  # noqa: E402
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


def test_compute_alpha_fade_in_out() -> None:
    renderer = IntroRenderer(200, 100)
    assert renderer.compute_alpha(0.0) == 0
    assert renderer.compute_alpha(0.5) == 255
    assert renderer.compute_alpha(1.0) == 0


def test_compute_alpha_custom_fade() -> None:
    config = IntroConfig(fade=lambda t: t)
    renderer = IntroRenderer(200, 100, config=config)
    assert renderer.compute_alpha(0.25) == int(0.5 * 255)


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

    renderer.draw(surface, ("A", "B"), 1.0)

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
