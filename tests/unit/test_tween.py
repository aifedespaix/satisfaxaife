from __future__ import annotations

from collections.abc import Callable

import pytest

from app.core.tween import (
    ease_in_out_cubic,
    ease_out_back,
    ease_out_elastic,
    linear,
)


@pytest.mark.parametrize(
    ("func", "expected_mid"),
    [
        (linear, 0.5),
        (ease_in_out_cubic, 0.5),
        (ease_out_back, 1.0876975),
        (ease_out_elastic, 1.015625),
    ],
)
def test_values(func: Callable[[float], float], expected_mid: float) -> None:
    assert func(0.0) == pytest.approx(0.0)
    assert func(0.5) == pytest.approx(expected_mid)
    assert func(1.0) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "func",
    [linear, ease_in_out_cubic, ease_out_back, ease_out_elastic],
)
def test_continuity(func: Callable[[float], float]) -> None:
    eps = 1e-5
    center = func(0.5)
    assert func(0.5 - eps) == pytest.approx(center, abs=1e-4)
    assert func(0.5 + eps) == pytest.approx(center, abs=1e-4)


@pytest.mark.parametrize(
    "func",
    [linear, ease_in_out_cubic, ease_out_back, ease_out_elastic],
)
def test_clamping_out_of_range(func: Callable[[float], float]) -> None:
    assert func(-1.0) == pytest.approx(0.0)
    assert func(2.0) == pytest.approx(1.0)
