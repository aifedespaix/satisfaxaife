from __future__ import annotations

import pytest

from app.core.config import settings
from app.core.utils import clamp, ping_pong, to_screen


def test_clamp() -> None:
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(11, 0, 10) == 10


def test_to_screen() -> None:
    assert to_screen((0.0, 0.0)) == (0, settings.height)
    assert to_screen((10.0, settings.height)) == (10, 0)


def test_ping_pong() -> None:
    assert ping_pong(0.0) == 0.0
    assert ping_pong(0.25) == pytest.approx(0.25)
    assert ping_pong(0.5) == pytest.approx(0.5)
    assert ping_pong(1.0) == 1.0
    assert ping_pong(1.5) == pytest.approx(0.5)
    assert ping_pong(2.0) == 0.0
