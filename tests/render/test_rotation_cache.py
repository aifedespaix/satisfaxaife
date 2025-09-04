from __future__ import annotations

import sys
import types
from collections.abc import Callable
from typing import Any

import pytest


@pytest.fixture()
def renderer_stub(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Any, type, list[int], list[tuple[tuple[float, float], int, Any]]]:
    class PygameStub(types.ModuleType):
        SRCALPHA: int
        init: Callable[[], None]
        font: Any
        display: Any
        image: Any
        draw: Any
        transform: Any
        Surface: type

    pygame_stub = PygameStub("pygame")
    pygame_stub.SRCALPHA = 0

    class Surface:
        def __init__(self, size: tuple[int, int], flags: int = 0) -> None:
            self._width, self._height = size

        def get_rect(self, *, center: tuple[float, float]) -> object:
            return types.SimpleNamespace(center=center)

        def blit(self, _sprite: object, _rect: object) -> None:  # pragma: no cover - stub
            pass

        def convert_alpha(self) -> Surface:
            return self

    pygame_stub.Surface = Surface
    pygame_stub.init = lambda: None
    pygame_stub.font = types.SimpleNamespace(init=lambda: None)
    pygame_stub.display = types.SimpleNamespace(set_mode=lambda size: None)
    pygame_stub.image = types.SimpleNamespace(load=lambda path: Surface((32, 32)))

    rotation_calls: list[int] = []
    glow_calls: list[tuple[tuple[float, float], int, Any]] = []

    def rotozoom(surface: Surface, angle: float, scale: float) -> Surface:
        rotation_calls.append(int(angle))
        return Surface((surface._width, surface._height))

    pygame_stub.draw = types.SimpleNamespace(circle=lambda *a, **k: None, line=lambda *a, **k: None)
    pygame_stub.transform = types.SimpleNamespace(
        rotozoom=rotozoom, smoothscale=lambda s, size: Surface(size)
    )

    sys.modules["pygame"] = pygame_stub
    sys.modules.pop("app.render.renderer", None)

    fake_theme = types.SimpleNamespace(
        team_a=types.SimpleNamespace(primary=(255, 0, 0)),
        team_b=types.SimpleNamespace(primary=(0, 255, 0)),
    )
    fake_settings = types.SimpleNamespace(
        width=200,
        height=200,
        theme=fake_theme,
        show_eyes=True,
        dt=1 / 60,
    )

    class _ConfigModule(types.ModuleType):
        settings: object

    fake_config = _ConfigModule("app.core.config")
    fake_config.settings = fake_settings
    sys.modules["app.core.config"] = fake_config

    from app.render.renderer import Renderer

    def fake_draw_glow(
        _surface: Any, center: tuple[float, float], radius: int, color: Any
    ) -> None:
        glow_calls.append((center, radius, color))

    monkeypatch.setattr("app.render.renderer.draw_glow", fake_draw_glow)

    renderer = Renderer(200, 200)
    return renderer, Surface, rotation_calls, glow_calls


def test_sprite_rotation_cached(
    renderer_stub: tuple[Any, type, list[int], list[tuple[tuple[float, float], int, Any]]]
) -> None:
    renderer, Surface, rotation_calls, _ = renderer_stub
    sprite = Surface((32, 32))
    renderer.draw_sprite(sprite, (0.0, 0.0), 0.1)
    renderer.draw_sprite(sprite, (0.0, 0.0), 0.12)
    renderer.draw_sprite(sprite, (0.0, 0.0), 0.5)
    renderer.draw_sprite(sprite, (0.0, 0.0), 0.5)
    assert rotation_calls == [355, 330]


def test_draw_sprite_with_aura(
    renderer_stub: tuple[Any, type, list[int], list[tuple[tuple[float, float], int, Any]]]
) -> None:
    renderer, Surface, _rotation_calls, glow_calls = renderer_stub
    sprite = Surface((32, 32))
    renderer.draw_sprite(sprite, (0.0, 0.0), 0.0, aura_color=(1, 2, 3), aura_radius=5)
    assert glow_calls == [((0.0, 0.0), 7, (1, 2, 3))]


def test_draw_projectile_with_aura(
    renderer_stub: tuple[Any, type, list[int], list[tuple[tuple[float, float], int, Any]]]
) -> None:
    renderer, _Surface, _rotation_calls, glow_calls = renderer_stub
    renderer.draw_projectile((1.0, 2.0), 5, (255, 255, 0), aura_color=(1, 2, 3))
    assert glow_calls == [((1.0, 2.0), 7, (1, 2, 3))]

