from __future__ import annotations

import pytest

from app.display import calculate_scale


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
