import pytest

from app.core.animation import Animation, Timeline


def test_animation_interpolates() -> None:
    anim = Animation(0.0, 10.0, 2.0)
    anim.update(1.0)
    assert anim.value == pytest.approx(5.0)
    assert anim.progress == pytest.approx(0.5)


def test_animation_cancel() -> None:
    anim = Animation(0.0, 10.0, 2.0)
    anim.cancel()
    anim.update(1.0)
    assert anim.finished
    assert anim.value == pytest.approx(0.0)


def test_timeline_chaining() -> None:
    first = Animation(0.0, 1.0, 1.0)
    second = Animation(1.0, 2.0, 1.0)
    tl = Timeline()
    tl.add(first)
    tl.add(second)
    tl.update(1.0)
    assert tl.current is second and not tl.finished
    tl.update(1.0)
    assert tl.finished
