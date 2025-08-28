from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

pygame_stub = cast(Any, types.ModuleType("pygame"))
pygame_stub.Surface = object
pygame_stub.surfarray = types.ModuleType("surfarray")
pygame_stub.surfarray.array3d = lambda *args, **kwargs: None
sys.modules.setdefault("pygame", pygame_stub)

np_stub = cast(Any, types.ModuleType("numpy"))
sys.modules.setdefault("numpy", np_stub)

from app.core.types import Damage  # noqa: E402
from app.game.match import Player, _MatchView  # noqa: E402
from app.world.entities import Ball  # noqa: E402
from app.world.physics import PhysicsWorld  # noqa: E402

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from app.ai.policy import SimplePolicy
    from app.audio import AudioEngine
    from app.render.renderer import Renderer
    from app.weapons.base import Weapon


class DummyRenderer:
    def add_impact(self, pos: tuple[float, float]) -> None:  # pragma: no cover - stub
        return

    def trigger_blink(
        self, color: tuple[int, int, int], intensity: int
    ) -> None:  # pragma: no cover - stub
        return


class DummyEngine:
    def __init__(self) -> None:
        self.paths: list[str] = []
        self.timestamps: list[float | None] = []

    def play_variation(
        self, path: str, volume: float | None = None, timestamp: float | None = None
    ) -> bool:
        self.paths.append(path)
        self.timestamps.append(timestamp)
        return True


def test_deal_damage_triggers_explosion_sound_on_death() -> None:
    world = PhysicsWorld()
    ball = Ball.spawn(world, (0.0, 0.0))
    weapon = cast("Weapon", object())
    policy = cast("SimplePolicy", object())
    player = Player(ball.eid, ball, weapon, policy, (1.0, 0.0), (255, 255, 255))
    dummy_engine = DummyEngine()
    engine = cast("AudioEngine", dummy_engine)
    renderer = cast("Renderer", DummyRenderer())
    view = _MatchView([player], [], world, renderer, engine)

    view.deal_damage(player.eid, Damage(amount=200.0), timestamp=1.23)

    path = Path("assets/balls/explose.ogg").as_posix()
    assert path in dummy_engine.paths
    assert dummy_engine.timestamps[dummy_engine.paths.index(path)] == 1.23
