"""Minimal stub of the :mod:`pymunk` API used in tests.

This stub provides lightweight implementations of the classes required by
unit tests.  It is *not* a full physics engine and only implements the
features exercised by the repository's tests.  The real Pymunk package
should be used for any production code.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence

# mypy: ignore-errors
from dataclasses import dataclass


@dataclass(slots=True)
class _Collision:
    """Collision result with intersection points."""

    points: list[int]


@dataclass(slots=True)
class BB:
    """Axis-aligned bounding box."""

    left: float
    bottom: float
    right: float
    top: float

    def intersects(self, other: BB) -> bool:
        """Return ``True`` if two bounding boxes overlap."""
        return not (
            self.right < other.left
            or self.left > other.right
            or self.top < other.bottom
            or self.bottom > other.top
        )


@dataclass(slots=True)
class Vec2:
    """2D vector with iterable behaviour."""

    x: float
    y: float

    def __iter__(self) -> Iterator[float]:
        yield self.x
        yield self.y

    def __getitem__(self, index: int) -> float:
        """Return a coordinate by ``index``.

        Parameters
        ----------
        index:
            ``0`` for ``x`` and ``1`` for ``y``.

        Raises
        ------
        IndexError
            If ``index`` is not ``0`` or ``1``.
        """
        if index == 0:
            return self.x
        if index == 1:
            return self.y
        raise IndexError("Vec2 index out of range")

    def normalized(self) -> Vec2:
        norm = (self.x * self.x + self.y * self.y) ** 0.5 or 1.0
        return Vec2(self.x / norm, self.y / norm)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)


class Body:
    """Simple rigid body supporting position and velocity."""

    def __init__(self, mass: float, moment: float) -> None:  # noqa: D401 - unused
        self._position = Vec2(0.0, 0.0)
        self._velocity = Vec2(0.0, 0.0)

    @property
    def position(self) -> Vec2:  # noqa: D401 - simple struct
        return self._position

    @position.setter
    def position(self, value: Iterable[float]) -> None:
        x, y = value
        self._position = Vec2(float(x), float(y))

    @property
    def velocity(self) -> Vec2:  # noqa: D401 - simple struct
        return self._velocity

    @velocity.setter
    def velocity(self, value: Iterable[float]) -> None:
        x, y = value
        self._velocity = Vec2(float(x), float(y))

    def apply_impulse_at_local_point(self, impulse: Iterable[float]) -> None:
        """Add an instantaneous velocity change in local coordinates.

        Parameters
        ----------
        impulse:
            Two-component impulse vector. The stub treats this vector as a
            direct change in velocity and ignores mass or rotational effects,
            mirroring :meth:`pymunk.Body.apply_impulse_at_local_point`.
        """
        vx, vy = impulse
        self._velocity = Vec2(
            self._velocity.x + float(vx),
            self._velocity.y + float(vy),
        )


class Shape:
    """Base collision shape."""

    def __init__(self, body: Body) -> None:
        self.body = body
        self.elasticity: float = 0.0
        self.friction: float = 0.0
        self.collision_type: int = 0
        self.sensor: bool = False

    @property
    def bb(self) -> BB:
        raise NotImplementedError

    def shapes_collide(self, other: Shape) -> _Collision:  # pragma: no cover - overridden
        return _Collision(points=[])


class Circle(Shape):
    """Circle collision shape."""

    def __init__(self, body: Body, radius: float) -> None:
        super().__init__(body)
        self.radius = radius

    @property
    def bb(self) -> BB:
        x = self.body.position.x
        y = self.body.position.y
        r = float(self.radius)
        return BB(x - r, y - r, x + r, y + r)

    def shapes_collide(self, other: Shape) -> _Collision:
        if isinstance(other, Circle):
            dx = self.body.position.x - other.body.position.x
            dy = self.body.position.y - other.body.position.y
            rad = float(self.radius) + float(other.radius)
            if dx * dx + dy * dy <= rad * rad:
                return _Collision(points=[1])
        return _Collision(points=[])


class Segment(Shape):
    """Static segment used for world boundaries."""

    def __init__(self, body: Body, a: Sequence[float], b: Sequence[float], radius: float) -> None:
        super().__init__(body)
        self.a = a
        self.b = b
        self.radius = radius

    @property
    def bb(self) -> BB:
        left = min(self.a[0], self.b[0]) - self.radius
        right = max(self.a[0], self.b[0]) + self.radius
        bottom = min(self.a[1], self.b[1]) - self.radius
        top = max(self.a[1], self.b[1]) + self.radius
        return BB(left, bottom, right, top)


def _reflect_velocity(velocity: Vec2, normal: Vec2, elasticity: float) -> Vec2:
    """Return ``velocity`` reflected around ``normal`` with ``elasticity``.

    The component of the velocity along ``normal`` is reversed and scaled by
    ``elasticity`` while the tangential component is preserved.  This mimics
    Pymunk's energy conserving, frictionless bounces against static segments.
    """

    vn = velocity.x * normal.x + velocity.y * normal.y
    if vn >= 0:
        # Already moving away from the wall; no change.
        return velocity
    scale = (1.0 + elasticity) * vn
    return Vec2(velocity.x - scale * normal.x, velocity.y - scale * normal.y)


def _resolve_circle_segment(circle: Circle, segment: Segment, prev: Vec2) -> None:
    """Clamp ``circle`` against ``segment`` and apply bounce when crossing.

    Parameters
    ----------
    circle:
        The dynamic shape to test.
    segment:
        Boundary segment.
    prev:
        Previous position of the circle's body before integration.
    """

    pos = circle.body.position
    radius = float(circle.radius)
    elasticity = circle.elasticity * segment.elasticity

    if segment.a[0] == segment.b[0]:
        # Vertical wall at x = segment.a[0]
        wall_x = segment.a[0]
        if prev.x >= wall_x and pos.x - radius < wall_x:
            circle.body.position = Vec2(wall_x + radius, pos.y)
            circle.body.velocity = _reflect_velocity(
                circle.body.velocity, Vec2(1.0, 0.0), elasticity
            )
        elif prev.x <= wall_x and pos.x + radius > wall_x:
            circle.body.position = Vec2(wall_x - radius, pos.y)
            circle.body.velocity = _reflect_velocity(
                circle.body.velocity, Vec2(-1.0, 0.0), elasticity
            )
    elif segment.a[1] == segment.b[1]:
        # Horizontal wall at y = segment.a[1]
        wall_y = segment.a[1]
        if prev.y >= wall_y and pos.y - radius < wall_y:
            circle.body.position = Vec2(pos.x, wall_y + radius)
            circle.body.velocity = _reflect_velocity(
                circle.body.velocity, Vec2(0.0, 1.0), elasticity
            )
        elif prev.y <= wall_y and pos.y + radius > wall_y:
            circle.body.position = Vec2(pos.x, wall_y - radius)
            circle.body.velocity = _reflect_velocity(
                circle.body.velocity, Vec2(0.0, -1.0), elasticity
            )


def moment_for_circle(mass: float, inner_radius: float, radius: float) -> float:  # noqa: D401 - placeholder
    """Return a placeholder moment for a circle."""
    return 0.0


class Space:
    """Container for bodies and shapes with naive integration."""

    def __init__(self) -> None:
        self.gravity = (0.0, 0.0)
        self.static_body = Body(0.0, 0.0)
        self._bodies: list[Body] = []
        self._shapes: list[Shape] = []

    def add(self, *objs: object) -> None:
        for obj in objs:
            if isinstance(obj, Body):
                self._bodies.append(obj)
            elif isinstance(obj, Shape):
                self._shapes.append(obj)

    def remove(self, *objs: object) -> None:
        for obj in objs:
            if isinstance(obj, Body) and obj in self._bodies:
                self._bodies.remove(obj)
            elif isinstance(obj, Shape) and obj in self._shapes:
                self._shapes.remove(obj)

    def step(self, dt: float) -> None:
        segments = [s for s in self._shapes if isinstance(s, Segment)]
        circles = {s.body: s for s in self._shapes if isinstance(s, Circle)}
        for body in self._bodies:
            prev = Vec2(body.position.x, body.position.y)
            body.position = (
                body.position.x + body.velocity.x * dt,
                body.position.y + body.velocity.y * dt,
            )
            circle = circles.get(body)
            if circle is None:
                continue
            for segment in segments:
                _resolve_circle_segment(circle, segment, prev)
