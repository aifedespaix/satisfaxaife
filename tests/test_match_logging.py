"""Verify logging of elapsed simulation seconds in GameController."""

from __future__ import annotations

import logging
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any, cast

import pygame
import pytest

from app.ai.stateful_policy import StatefulPolicy
from app.audio import AudioEngine, BallAudio
from app.core.types import EntityId
from app.game.controller import GameController, MatchTimeout, Player
from app.intro import IntroManager
from app.render.hud import Hud
from app.render.renderer import Renderer
from app.video.recorder import RecorderProtocol
from app.weapons.base import Weapon
from app.world.entities import Ball
from app.world.physics import PhysicsWorld


class DummyWorld:
    def set_projectile_removed_callback(self, _cb: Callable[[Any], None]) -> None:
        return

    def set_context(self, _view: object, _timestamp: float) -> None:  # pragma: no cover - stub
        return

    def step(self, _dt: float, _substeps: int) -> None:  # pragma: no cover - stub
        return


class DummyWeapon:
    speed: float = 0.0
    audio = SimpleNamespace(stop_idle=lambda _timestamp: None)

    def step(self, _dt: float) -> None:  # pragma: no cover - stub
        return

    def update(
        self, _owner: EntityId, _view: object, _dt: float
    ) -> None:  # pragma: no cover - stub
        return

    def parry(self, _owner: EntityId, _view: object) -> None:  # pragma: no cover - stub
        return

    def trigger(
        self, _owner: EntityId, _view: object, _direction: tuple[float, float]
    ) -> None:  # pragma: no cover - stub
        return


class DummyPolicy:
    def decide(
        self, _eid: EntityId, _view: object, _speed: float
    ) -> tuple[tuple[float, float], tuple[float, float], bool, bool]:  # pragma: no cover - stub
        return (0.0, 0.0), (1.0, 0.0), False, False

    def dash_direction(
        self, _eid: EntityId, _view: object, _now: float, _can_dash: bool
    ) -> None:  # pragma: no cover - stub
        return None


class DummyBallAudio:
    def on_hit(self, _timestamp: float | None = None) -> None:  # pragma: no cover - stub
        return

    def on_explode(self, _timestamp: float | None = None) -> None:  # pragma: no cover - stub
        return

    def stop_idle(self, _timestamp: float | None = None) -> None:  # pragma: no cover - stub
        return


class DummyBall:
    body = SimpleNamespace(position=SimpleNamespace(x=0.0, y=0.0), velocity=(0.0, 0.0))
    shape = SimpleNamespace(radius=1)
    stats = SimpleNamespace(max_health=100.0)
    health: float = 100.0

    def cap_speed(self) -> None:  # pragma: no cover - stub
        return


def _make_player(eid: int) -> Player:
    ball = cast(Ball, DummyBall())
    weapon = cast(Weapon, DummyWeapon())
    policy = cast(StatefulPolicy, DummyPolicy())
    audio = cast(BallAudio, DummyBallAudio())
    return Player(EntityId(eid), ball, weapon, policy, (1.0, 0.0), (0, 0, 0), audio)


def test_logs_each_second(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    world = cast(PhysicsWorld, DummyWorld())
    renderer = cast(Renderer, SimpleNamespace())
    hud = cast(Hud, SimpleNamespace())
    engine = cast(AudioEngine, SimpleNamespace())
    recorder = cast(
        RecorderProtocol,
        SimpleNamespace(add_frame=lambda _frame: None, close=lambda _audio=None, rate=48_000: None),
    )
    intro = cast(IntroManager, SimpleNamespace())

    controller = GameController(
        "a",
        "b",
        [_make_player(1), _make_player(2)],
        world,
        renderer,
        hud,
        engine,
        recorder,
        intro,
        max_seconds=2,
    )
    monkeypatch.setattr(controller, "_update_players", lambda _now: None)
    monkeypatch.setattr(controller, "_update_effects", lambda _now: None)
    monkeypatch.setattr(controller, "_render_frame", lambda: None)
    monkeypatch.setattr(controller, "_capture_frame", lambda: None)
    monkeypatch.setattr(pygame.event, "get", lambda: [])

    with caplog.at_level(logging.INFO, logger="app.game.controller"):
        with pytest.raises(MatchTimeout):
            controller._run_match_loop(0.0)

    messages = [record.message for record in caplog.records]
    assert "Simulation time: 1 s" in messages
    assert "Simulation time: 2 s" in messages
