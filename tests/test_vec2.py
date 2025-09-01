from __future__ import annotations

import pytest

from pymunk import Vec2


def test_vec2_index_access() -> None:
    vec = Vec2(1.5, -2.0)
    assert vec[0] == 1.5
    assert vec[1] == -2.0


@pytest.mark.parametrize("index", [-1, 2])
def test_vec2_index_error(index: int) -> None:
    vec = Vec2(0.0, 0.0)
    with pytest.raises(IndexError):
        _ = vec[index]
