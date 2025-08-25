from __future__ import annotations

from app.core.config import settings
from app.core.utils import clamp, ease_out_quad, to_screen


def test_clamp() -> None:
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(11, 0, 10) == 10


def test_ease_out_quad() -> None:
    assert ease_out_quad(0.0) == 0.0
    assert ease_out_quad(1.0) == 1.0


def test_to_screen() -> None:
    assert to_screen((0.0, 0.0)) == (0, settings.height)
    assert to_screen((42.5, 100.0))[0] == 42
