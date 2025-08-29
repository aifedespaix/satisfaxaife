"""Ensure idle sounds are truncated at death."""

from __future__ import annotations

import os
import time
from typing import cast

import numpy as np

from app.ai.policy import SimplePolicy
from app.audio import AudioEngine, reset_default_engine
from app.audio.balls import BallAudio
from app.audio.weapons import WeaponAudio
from app.core.types import Color, Damage, EntityId, Vec2
from app.game.match import Player, _MatchView
from app.weapons.base import Weapon, WorldView
from app.world.entities import Ball
from app.world.physics import PhysicsWorld

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


class SilentBallAudio:
    def on_explode(self, timestamp: float | None = None) -> None:  # noqa: D401
        return None


class StubRenderer:
    def add_impact(self, pos: Vec2, duration: float = 0.0) -> None:  # noqa: D401
        return None

    def trigger_blink(self, color: Color, amount: int) -> None:  # noqa: D401
        return None


class IdleWeapon(Weapon):
    def __init__(self, audio: WeaponAudio) -> None:
        super().__init__(name="idle", cooldown=0.0, damage=Damage(500))
        self.audio = audio

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:  # noqa: D401
        return None


def test_idle_sound_truncated_on_death() -> None:
    engine = AudioEngine()
    engine.start_capture()
    weapon_audio = WeaponAudio("melee", "katana", engine=engine, idle_gap=0.01)
    weapon_audio.start_idle(timestamp=0.0)
    time.sleep(0.05)
    weapon = IdleWeapon(weapon_audio)

    world = PhysicsWorld()
    ball = Ball.spawn(world, (0.0, 0.0))
    player = Player(
        eid=ball.eid,
        ball=ball,
        weapon=weapon,
        policy=SimplePolicy("aggressive"),
        face=(1.0, 0.0),
        color=(255, 255, 255),
        audio=cast(BallAudio, SilentBallAudio()),
    )
    renderer = cast(Renderer, StubRenderer())
    view = _MatchView([player], [], world, renderer, engine)

    view.deal_damage(player.eid, Damage(500), timestamp=0.2)

    audio = engine.end_capture()
    cut = int(0.2 * AudioEngine.SAMPLE_RATE)
    assert audio.shape[0] >= cut
    if audio.shape[0] > cut:
        assert not np.any(audio[cut:])

    weapon_audio.stop_idle()
    engine.shutdown()
    reset_default_engine()

