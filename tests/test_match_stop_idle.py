"""Ensure stopping idle audio does not silence the explosion."""

from __future__ import annotations

import os
import time
from typing import Any, cast

from app.audio import AudioEngine, reset_default_engine
from app.audio.balls import BallAudio
from app.audio.weapons import WeaponAudio
from app.core.types import Color, Damage, EntityId, TeamId, Vec2
from app.game.match import Player, _MatchView
from app.world.entities import Ball
from app.world.physics import PhysicsWorld

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


class StubRenderer:
    def add_impact(self, pos: Vec2, duration: float = 0.0) -> None:  # noqa: D401
        return None

    def trigger_blink(self, color: Color, amount: int) -> None:  # noqa: D401
        return None


class IdleWeapon:
    def __init__(self, audio: WeaponAudio) -> None:
        self.audio = audio
        self.cooldown = 0.0
        self.name = "idle"

    def _fire(self, owner: EntityId, view: Any, direction: Vec2) -> None:  # noqa: D401
        return None


def test_idle_sound_truncated_on_death() -> None:
    engine = AudioEngine()
    engine.start_capture()
    weapon_audio = WeaponAudio("melee", "katana", engine=engine, idle_gap=0.01)
    weapon_audio.start_idle(timestamp=0.0)
    time.sleep(0.05)
    weapon = cast(Any, IdleWeapon(weapon_audio))

    world = PhysicsWorld()
    ball = Ball.spawn(world, (0.0, 0.0))

    class DummyPolicy:
        pass

    player = Player(
        eid=ball.eid,
        ball=ball,
        weapon=weapon,
        policy=cast(Any, DummyPolicy()),
        face=(1.0, 0.0),
        color=(255, 255, 255),
        team=TeamId(0),
        audio=BallAudio(engine=engine),
    )
    renderer = cast(Any, StubRenderer())
    view = _MatchView([player], [], world, renderer, engine)

    view.deal_damage(player.eid, Damage(500), timestamp=0.2)

    audio = engine.end_capture()
    cut = int(0.2 * AudioEngine.SAMPLE_RATE)
    assert audio.shape[0] >= cut
    if audio.shape[0] > cut:
        assert audio[cut:].any()

    weapon_audio.stop_idle()
    engine.shutdown()
    reset_default_engine()
