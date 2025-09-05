from __future__ import annotations

import types
from typing import Any, cast

from app.core.types import Damage, EntityId
from app.game.controller import Player
from tests.helpers import make_controller, make_player


class DummyEffect:
    def __init__(self, owner: EntityId) -> None:
        self.owner = owner

    def collides(self, _view: Any, _pos: Any, _radius: float) -> bool:
        return True

    def on_hit(self, view: Any, target: EntityId, timestamp: float) -> bool:
        view.deal_damage(target, Damage(10.0), timestamp)
        return True


def _setup_players(team_b: int) -> tuple[Any, Player, Player]:
    player_a = make_player(1, 0.0, team=0)
    player_b = make_player(2, 60.0, team=team_b)
    stub_audio = types.SimpleNamespace(
        on_hit=lambda *_a, **_k: None,
        on_explode=lambda *_a, **_k: None,
        stop_idle=lambda *_a, **_k: None,
    )
    player_a.audio = cast(Any, stub_audio)
    player_b.audio = cast(Any, stub_audio)
    controller = make_controller(player_a, player_b)
    renderer = types.SimpleNamespace(
        add_impact=lambda *_a, **_k: None,
        trigger_blink=lambda *_a, **_k: None,
        trigger_hit_flash=lambda *_a, **_k: None,
        clear=lambda: None,
        draw_ball=lambda *_a, **_k: None,
        draw_impacts=lambda: None,
        update_hp=lambda *_a, **_k: None,
    )
    controller.renderer = cast(Any, renderer)
    controller.view.renderer = cast(Any, renderer)
    return controller, player_a, player_b


def test_effect_hits_enemy() -> None:
    controller, player_a, player_b = _setup_players(team_b=1)
    eff = DummyEffect(player_a.eid)
    controller.effects.append(cast(Any, eff))
    controller._resolve_effect_hits(0.0)
    assert player_b.ball.health == 90.0


def test_effect_heals_ally() -> None:
    controller, player_a, player_b = _setup_players(team_b=0)
    player_b.ball.health = 90.0
    eff = DummyEffect(player_a.eid)
    controller.effects.append(cast(Any, eff))
    controller._resolve_effect_hits(0.0)
    assert player_b.ball.health == 100.0
