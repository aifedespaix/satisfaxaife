"""Generic animation utilities with composable timelines."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .tween import linear

Easing = Callable[[float], float]
Interpolator = Callable[[float, float, float], float]


def _lerp(start: float, end: float, t: float) -> float:
    """Return the linear interpolation between ``start`` and ``end``."""
    return start + (end - start) * t


@dataclass
class Animation:
    """Interpolate a value from ``start`` to ``end`` over ``duration`` seconds."""

    start: float
    end: float
    duration: float
    easing: Easing = linear
    interpolate: Interpolator = _lerp
    elapsed: float = 0.0
    finished: bool = False

    def update(self, dt: float) -> None:
        """Advance the animation by ``dt`` seconds."""
        if self.finished:
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.elapsed = self.duration
            self.finished = True

    @property
    def progress(self) -> float:
        """Return the normalised progress in ``[0, 1]``."""
        if self.duration == 0.0:
            return 1.0
        return min(self.elapsed / self.duration, 1.0)

    @property
    def value(self) -> float:
        """Return the interpolated value at the current progress."""
        t = self.easing(self.progress)
        return self.interpolate(self.start, self.end, t)

    def cancel(self) -> None:
        """Stop the animation immediately."""
        self.finished = True


class Animator:
    """Update and query multiple animations in parallel."""

    def __init__(self) -> None:
        self._animations: dict[str, Animation] = {}

    def add(self, name: str, animation: Animation) -> None:
        self._animations[name] = animation

    def update(self, dt: float) -> None:
        for key in list(self._animations.keys()):
            anim = self._animations[key]
            anim.update(dt)
            if anim.finished:
                self._animations.pop(key)

    def get(self, name: str) -> Animation | None:
        return self._animations.get(name)

    def value(self, name: str, default: float) -> float:
        anim = self._animations.get(name)
        return anim.value if anim is not None else default

    def cancel(self, name: str) -> None:
        anim = self._animations.pop(name, None)
        if anim is not None:
            anim.cancel()


class Timeline:
    """Chain animations sequentially."""

    def __init__(self) -> None:
        self._queue: list[Animation] = []
        self._current: Animation | None = None
        self.finished: bool = False

    def add(self, animation: Animation) -> None:
        self._queue.append(animation)
        if self._current is None:
            self._current = self._queue.pop(0)

    @property
    def current(self) -> Animation | None:
        return self._current

    def update(self, dt: float) -> None:
        if self.finished or self._current is None:
            return
        self._current.update(dt)
        if self._current.finished:
            if self._queue:
                self._current = self._queue.pop(0)
            else:
                self._current = None
                self.finished = True

    def cancel(self) -> None:
        """Cancel the timeline and all pending animations."""
        self._queue.clear()
        self._current = None
        self.finished = True

__all__ = ["Animation", "Animator", "Timeline"]

