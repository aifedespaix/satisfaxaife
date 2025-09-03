import math
import sys
import types
import typing
from pathlib import Path
from types import SimpleNamespace

import pytest

# Stub pygame and related modules before importing the weapon
pygame = sys.modules.setdefault("pygame", types.ModuleType("pygame"))
pygame.Surface = object  # type: ignore[attr-defined]
pygame.image = SimpleNamespace(load=lambda *_a, **_k: object())  # type: ignore[attr-defined]
pygame.transform = SimpleNamespace(smoothscale=lambda surf, size: surf)  # type: ignore[attr-defined]
pygame.display = SimpleNamespace(get_surface=lambda: object(), set_mode=lambda size: None)  # type: ignore[attr-defined]
pygame.get_init = lambda: True  # type: ignore[attr-defined]


class _Surface:
    def get_width(self) -> int:  # pragma: no cover - simple stub
        return 10

    def get_height(self) -> int:  # pragma: no cover - simple stub
        return 10

    def get_size(self) -> tuple[int, int]:  # pragma: no cover - simple stub
        return (10, 10)


def _load_sprite(*_a: object, **_k: object) -> _Surface:  # pragma: no cover - simple stub
    return _Surface()


sprites_mod = types.ModuleType("app.render.sprites")
sprites_mod.load_sprite = _load_sprite  # type: ignore[attr-defined]
sprites_mod.ASSET_DIR = Path(".")  # type: ignore[attr-defined]
sys.modules.setdefault("app.render.sprites", sprites_mod)

assets_mod = types.ModuleType("app.weapons.assets")
assets_mod.load_weapon_sprite = _load_sprite  # type: ignore[attr-defined]
sys.modules.setdefault("app.weapons.assets", assets_mod)

audio_mod = types.ModuleType("app.audio.weapons")


class _WeaponAudio:
    def __init__(self, *_a: object, **_k: object) -> None:  # noqa: D401
        return None

    def on_throw(self, *_a: object, **_k: object) -> None:  # noqa: D401
        return None

    def start_idle(self) -> None:  # pragma: no cover - unused
        return None

    def stop_idle(self, timestamp: float | None = None, *, disable: bool = False) -> None:  # pragma: no cover - unused
        return None


audio_mod.WeaponAudio = _WeaponAudio  # type: ignore[attr-defined]
audio_mod.get_default_engine = lambda: object()  # type: ignore[attr-defined]
audio_mod.reset_default_engine = lambda: None  # type: ignore[attr-defined]
sys.modules.setdefault("app.audio.weapons", audio_mod)

recorder_mod = types.ModuleType("app.video.recorder")
class _RecorderProtocol(typing.Protocol):
    def add_frame(self, frame: object) -> None: ...
    def close(self, audio: object | None = None, rate: int = 48_000) -> None: ...
recorder_mod.RecorderProtocol = _RecorderProtocol  # type: ignore[attr-defined]
sys.modules.setdefault("app.video.recorder", recorder_mod)

slowmo_mod = types.ModuleType("app.video.slowmo")
slowmo_mod.append_slowmo_ending = lambda *a, **k: None  # type: ignore[attr-defined]
sys.modules.setdefault("app.video.slowmo", slowmo_mod)

from app.weapons.bazooka import Bazooka  # noqa: E402
from app.weapons.effects import AimedSprite  # noqa: E402
from app.world.entities import DEFAULT_BALL_RADIUS  # noqa: E402
from tests.helpers import make_controller, make_player  # noqa: E402


@pytest.mark.parametrize("enemy_x", [100.0, 200.0])
def test_bazooka_effect_respawns(enemy_x: float) -> None:
    weapon = Bazooka()
    weapon._timer = 1.0  # prevent automatic firing during the test
    player_a = make_player(1, 0.0)
    player_a.weapon = weapon
    player_b = make_player(2, enemy_x)

    class _Policy:
        def decide(
            self, _eid: int, _view: object, _now: float, _speed: float
        ) -> tuple[tuple[float, float], tuple[float, float], bool]:
            return (0.0, 0.0), (1.0, 0.0), False

        def dash_direction(
            self, _eid: int, _view: object, _now: float, _can_dash: object
        ) -> None:
            return None

    policy = typing.cast(typing.Any, _Policy())
    player_a.policy = policy
    player_b.policy = typing.cast(typing.Any, _Policy())

    controller = make_controller(player_a, player_b)

    controller._update_players(0.0)
    controller._step_effects()
    assert controller.effects, "Effect should spawn after update"
    first = controller.effects[0]
    assert isinstance(first, AimedSprite)
    assert first.sprite is not None
    assert math.isclose(first.offset, DEFAULT_BALL_RADIUS * 1.5)

    controller.effects.clear()
    controller._update_players(0.0)
    controller._step_effects()
    assert controller.effects, "Effect should respawn when removed"
    new_eff = controller.effects[0]
    assert isinstance(new_eff, AimedSprite)
    assert new_eff.sprite is not None
    assert math.isclose(new_eff.offset, DEFAULT_BALL_RADIUS * 1.5)
    assert weapon._effect is new_eff
