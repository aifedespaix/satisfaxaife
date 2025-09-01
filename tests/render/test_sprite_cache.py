from __future__ import annotations

import sys
import types
from collections.abc import Callable
from typing import Any

import pytest


def test_ball_sprite_scaling_cached(monkeypatch: pytest.MonkeyPatch) -> None:
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

        def get_width(self) -> int:
            return self._width

        def get_rect(self, *, center: tuple[float, float]) -> object:
            return types.SimpleNamespace(center=center)

        def blit(self, _sprite: object, _rect: object) -> None:
            pass

        def convert_alpha(self) -> Surface:
            return self

    pygame_stub.Surface = Surface
    pygame_stub.init = lambda: None
    pygame_stub.font = types.SimpleNamespace(init=lambda: None)
    pygame_stub.display = types.SimpleNamespace(set_mode=lambda size: None)
    pygame_stub.image = types.SimpleNamespace(load=lambda path: Surface((32, 32)))
    pygame_stub.draw = types.SimpleNamespace(circle=lambda *a, **k: None)
    pygame_stub.transform = types.SimpleNamespace(smoothscale=lambda surf, size: Surface(size))

    sys.modules["pygame"] = pygame_stub
    pygame = pygame_stub
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

    renderer = Renderer(200, 200)
    team_color = fake_theme.team_a.primary
    base_width = renderer._ball_sprites[team_color].get_width()
    radius_a = base_width // 2 + 1
    radius_b = radius_a + 5
    calls: list[tuple[int, int]] = []
    original: Callable[[Surface, tuple[int, int]], Surface] = pygame.transform.smoothscale

    def tracking(surface: Surface, size: tuple[int, int]) -> Surface:
        calls.append(size)
        return original(surface, size)

    monkeypatch.setattr(pygame.transform, "smoothscale", tracking)

    renderer.draw_ball((50.0, 50.0), radius_a, (255, 255, 255), team_color)
    renderer.draw_ball((50.0, 50.0), radius_a, (255, 255, 255), team_color)
    renderer.draw_ball((50.0, 50.0), radius_b, (255, 255, 255), team_color)
    renderer.draw_ball((50.0, 50.0), radius_b, (255, 255, 255), team_color)

    assert calls == [(radius_a * 2, radius_a * 2), (radius_b * 2, radius_b * 2)]
