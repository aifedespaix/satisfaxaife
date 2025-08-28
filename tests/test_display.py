from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from app.display import Display, calculate_scale


@pytest.mark.parametrize(
    ("window", "expected"),
    [
        ((1080, 1920), 1.0),
        ((540, 960), 0.5),
        ((1920, 1080), 0.5625),
        ((3840, 2160), 1.125),
    ],
)
def test_calculate_scale(window: tuple[int, int], expected: float) -> None:
    assert calculate_scale(window, (1080, 1920)) == pytest.approx(expected)


def test_calculate_scale_invalid() -> None:
    with pytest.raises(ValueError):
        calculate_scale((0, 100), (1080, 1920))


def test_display_initial_window_scaled(monkeypatch: pytest.MonkeyPatch) -> None:
    info = SimpleNamespace(current_w=1920, current_h=1080)
    monkeypatch.setattr(pygame.display, "Info", lambda: info)

    captured: dict[str, tuple[int, int]] = {}

    class FakeSurface:
        def __init__(self, size: tuple[int, int]):
            self._size = size

        def get_size(self) -> tuple[int, int]:
            return self._size

    def fake_set_mode(size: tuple[int, int], flags: int) -> FakeSurface:
        captured["size"] = size
        return FakeSurface(size)

    monkeypatch.setattr(pygame.display, "set_mode", fake_set_mode)

    Display(1080, 1920)

    assert captured["size"] == (607, 1080)


def test_present_letterboxing(monkeypatch: pytest.MonkeyPatch) -> None:
    info = SimpleNamespace(current_w=1920, current_h=1080)
    monkeypatch.setattr(pygame.display, "Info", lambda: info)

    class FakeSurface:
        def __init__(self, size: tuple[int, int]):
            self._size = size
            self.blit_calls: list[tuple[object, tuple[int, int]]] = []

        def get_size(self) -> tuple[int, int]:
            return self._size

        def fill(self, color: tuple[int, int, int]) -> None:  # pragma: no cover - trivial
            pass

        def blit(self, surf: object, offset: tuple[int, int]) -> None:
            self.blit_calls.append((surf, offset))

    window = FakeSurface((1920, 1080))
    monkeypatch.setattr(pygame.display, "set_mode", lambda size, flags: window)
    monkeypatch.setattr(pygame.display, "get_surface", lambda: window)
    monkeypatch.setattr(pygame.display, "flip", lambda: None)

    scaled: dict[str, object] = {}

    def fake_smoothscale(surface: FakeSurface, size: tuple[int, int]) -> FakeSurface:
        scaled_surface = FakeSurface(size)
        scaled["size"] = size
        return scaled_surface

    monkeypatch.setattr(pygame.transform, "smoothscale", fake_smoothscale)

    display = Display(1080, 1920)
    source = FakeSurface((1080, 1920))
    display.present(source)

    assert scaled["size"] == (607, 1080)
    assert window.blit_calls[0][1] == (656, 0)
