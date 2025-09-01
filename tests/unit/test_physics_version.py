import pytest

pymunk = pytest.importorskip("pymunk")

from app.world import physics  # noqa: E402


def test_version_helper_parses_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fallback parsing uses ``__version__`` when ``version_info`` is absent."""

    class FakePymunk:
        __version__ = "6.1"

    monkeypatch.setattr(physics, "pymunk", FakePymunk, raising=False)
    version, version_str = physics._get_pymunk_version()

    assert version == (6, 1)
    assert version_str == "6.1"


def test_init_raises_runtime_error_for_old_pymunk(monkeypatch: pytest.MonkeyPatch) -> None:
    """PhysicsWorld refuses to run with unsupported pymunk versions."""
    monkeypatch.setattr(physics, "PYMUNK_VERSION", (6, 0))
    with pytest.raises(RuntimeError, match="pymunk >= 7.0"):
        physics.PhysicsWorld()


def test_register_handlers_falls_back_when_add_handler_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legacy collision_handler API is used when add_collision_handler is absent."""

    class FakeHandler:
        def __init__(self) -> None:
            self.begin = None

    class FakeSpace:
        def __init__(self) -> None:
            self.gravity = (0.0, 0.0)
            self.handler_called = False
            self.handler: FakeHandler | None = None

        def collision_handler(self, a: int, b: int) -> FakeHandler:
            self.handler_called = True
            self.handler = FakeHandler()
            return self.handler

        def add(self, *args: object) -> None:  # pragma: no cover - not used in test
            pass

        def step(self, _dt: float) -> None:  # pragma: no cover - not used in test
            pass

    fake_space = FakeSpace()
    monkeypatch.setattr(physics.pymunk, "Space", lambda: fake_space)  # type: ignore[attr-defined]
    monkeypatch.setattr(physics, "PYMUNK_VERSION", (7, 0))

    class NoBoundsWorld(physics.PhysicsWorld):
        def _add_bounds(self) -> None:  # pragma: no cover - avoids pymunk deps
            pass

    world = NoBoundsWorld()

    assert fake_space.handler_called
    assert fake_space.handler is not None
    assert fake_space.handler.begin is world._handle_projectile_hit
