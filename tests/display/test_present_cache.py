from __future__ import annotations

import os
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from app.display import Display


def test_present_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    info = SimpleNamespace(current_w=1920, current_h=1080)
    display_ns = SimpleNamespace()
    monkeypatch.setattr(pygame, "display", display_ns, raising=False)
    monkeypatch.setattr(display_ns, "Info", lambda: info, raising=False)
    monkeypatch.setattr(pygame, "RESIZABLE", 0, raising=False)
    monkeypatch.setattr(pygame, "FULLSCREEN", 0, raising=False)

    class FakeSurface:
        def __init__(self, size: tuple[int, int]):
            self._size = size
            self.blit_calls: list[tuple[object, tuple[int, int]]] = []

        def get_size(self) -> tuple[int, int]:
            return self._size

        def fill(self, color: tuple[int, int, int]) -> None:  # pragma: no cover
            pass

        def blit(self, surf: object, offset: tuple[int, int]) -> None:
            self.blit_calls.append((surf, offset))

    window = FakeSurface((1920, 1080))
    monkeypatch.setattr(display_ns, "set_mode", lambda size, flags: window, raising=False)
    monkeypatch.setattr(display_ns, "get_surface", lambda: window, raising=False)
    monkeypatch.setattr(display_ns, "flip", lambda: None, raising=False)

    calls = {"count": 0}
    transform_ns = SimpleNamespace()
    monkeypatch.setattr(pygame, "transform", transform_ns, raising=False)

    def fake_smoothscale(surface: FakeSurface, size: tuple[int, int]) -> FakeSurface:
        calls["count"] += 1
        return FakeSurface(size)

    monkeypatch.setattr(transform_ns, "smoothscale", fake_smoothscale, raising=False)

    display = Display(1080, 1920)
    source = FakeSurface((1080, 1920))

    display.present(source)
    display.present(source)
    assert calls["count"] == 1

    window._size = (1280, 720)
    display.present(source)
    assert calls["count"] == 2
