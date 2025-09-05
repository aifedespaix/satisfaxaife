from __future__ import annotations

from types import SimpleNamespace
from typing import Any, cast

import pygame
import pytest

from app.core.types import TeamId
from app.game.controller import GameController
from tests.helpers import make_player


class DummyWorld:
    """Physics world stub used for isolated controller testing."""

    def set_projectile_removed_callback(self, _cb: Any) -> None:  # pragma: no cover - stub
        return None

    def set_context(self, _view: object, _timestamp: float) -> None:  # pragma: no cover - stub
        return None

    def step(self, _dt: float, _substeps: int) -> None:  # pragma: no cover - stub
        return None


def test_team_victory(monkeypatch: pytest.MonkeyPatch) -> None:
    """Match ends when one team loses all its players."""

    p1 = make_player(1, x=0.0, team=0)
    p2 = make_player(2, x=0.0, team=0)
    p3 = make_player(3, x=0.0, team=1)

    world = cast(Any, DummyWorld())
    renderer = cast(Any, SimpleNamespace())
    hud = cast(Any, SimpleNamespace())
    engine = cast(Any, SimpleNamespace())
    recorder = cast(Any, SimpleNamespace(add_frame=lambda *_a: None, close=lambda **_k: None))
    intro = cast(Any, SimpleNamespace())

    controller = GameController("a", "b", [p1, p2, p3], world, renderer, hud, engine, recorder, intro)

    monkeypatch.setattr(pygame.event, "get", lambda: [])
    monkeypatch.setattr(controller, "_step_effects", lambda: None)
    monkeypatch.setattr(controller, "_deflect_projectiles", lambda _now: None)
    monkeypatch.setattr(controller, "_resolve_dash_collision", lambda _p, _now: None)
    monkeypatch.setattr(controller, "_resolve_effect_hits", lambda _now: None)
    monkeypatch.setattr(controller, "_render_frame", lambda: None)
    monkeypatch.setattr(controller, "_capture_frame", lambda: None)
    monkeypatch.setattr(controller, "_play_winner_sequence", lambda: None)

    def kill_enemy(_now: float) -> None:
        p3.alive = False

    monkeypatch.setattr(controller, "_update_players", kill_enemy)

    controller._run_match_loop(0.0)

    assert controller.winner_team == TeamId(0)

