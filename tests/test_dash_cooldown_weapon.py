"""Tests for dash cooldown configuration based on weapon range."""

from __future__ import annotations

from types import SimpleNamespace
from typing import cast

from app.ai.stateful_policy import StatefulPolicy
from app.audio import BallAudio
from app.core.types import Damage, EntityId
from app.game.controller import Player
from app.game.dash import Dash
from app.weapons.base import Weapon
from app.world.entities import Ball


def test_dash_cooldown_depends_on_weapon_range() -> None:
    """Distant weapons impose a longer dash cooldown."""

    ball = cast(Ball, SimpleNamespace())
    policy = cast(StatefulPolicy, SimpleNamespace())
    audio = cast(BallAudio, SimpleNamespace())

    contact_weapon = Weapon("contact", 0.0, Damage(1.0), range_type="contact")
    distant_weapon = Weapon("distant", 0.0, Damage(1.0), range_type="distant")

    contact_player = Player(EntityId(1), ball, contact_weapon, policy, (0.0, 0.0), (0, 0, 0), audio)
    distant_player = Player(EntityId(2), ball, distant_weapon, policy, (0.0, 0.0), (0, 0, 0), audio)

    base = Dash().cooldown
    assert contact_player.dash.cooldown == base
    assert distant_player.dash.cooldown == base * 2.0
