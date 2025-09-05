from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import cast

import pytest

from app.ai.stateful_policy import StatefulPolicy
from app.audio import AudioEngine, BallAudio
from app.core.types import EntityId, TeamId
from app.game.controller import GameController, MatchTimeout, Player
from app.intro import IntroManager
from app.render.hud import Hud
from app.render.renderer import Renderer
from app.video.recorder import RecorderProtocol
from app.weapons.base import Weapon
from app.world.entities import Ball
from app.world.physics import PhysicsWorld


class DummyWorld:
    def set_projectile_removed_callback(self, _cb: object) -> None:  # pragma: no cover - stub
        return None


class DummyWeapon:
    range_type = "contact"


class DummyPolicy: ...


class DummyBallAudio: ...


class DummyBall:
    body = SimpleNamespace(position=SimpleNamespace(x=0.0, y=0.0))
    shape = SimpleNamespace(radius=1)
    stats = SimpleNamespace(max_health=100.0)
    health: float = 100.0


def _make_player(eid: int) -> Player:
    ball = cast(Ball, DummyBall())
    weapon = cast(Weapon, DummyWeapon())
    policy = cast(StatefulPolicy, DummyPolicy())
    audio = cast(BallAudio, DummyBallAudio())
    return Player(
        EntityId(eid), ball, weapon, policy, (1.0, 0.0), (0, 0, 0), TeamId(eid % 2), audio
    )


def test_matchtimeout_not_masked_by_teardown_error(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    world = cast(PhysicsWorld, DummyWorld())
    renderer = cast(Renderer, SimpleNamespace())
    hud = cast(Hud, SimpleNamespace())
    engine = cast(AudioEngine, SimpleNamespace(start_capture=lambda: None))
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
    )

    monkeypatch.setattr(controller, "_run_intro", lambda _positions: 0.0)

    def raise_timeout(_elapsed: float) -> None:
        raise MatchTimeout("boom")

    monkeypatch.setattr(controller, "_run_match_loop", raise_timeout)

    def failing_teardown(_elapsed: float) -> None:
        raise RuntimeError("teardown failure")

    monkeypatch.setattr(controller, "_teardown", failing_teardown)

    with caplog.at_level(logging.ERROR, logger="app.game.controller"):
        with pytest.raises(MatchTimeout):
            controller.run()

    assert any("Error during teardown" in record.message for record in caplog.records)
