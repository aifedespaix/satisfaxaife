from __future__ import annotations

import pytest

from app.core.config import settings
from app.core.types import Damage
from app.game.match import create_controller
from app.render.renderer import Renderer
from app.video.recorder import NullRecorder


def test_owner_effects_removed_on_death(monkeypatch: pytest.MonkeyPatch) -> None:
    """Effects tied to a player disappear immediately when the player dies.

    Reproduces the case where a knife's orbiting blade could keep spinning
    after its owner was killed in 2v2+. We simulate a simple 1v1 for
    determinism: spawn the knife effect, kill the owner, and ensure no
    remaining effect references that owner.
    """

    # Ensure a minimal setup and prevent stray sounds/IO
    monkeypatch.setattr(settings, "team_a_count", 1)
    monkeypatch.setattr(settings, "team_b_count", 1)

    recorder = NullRecorder()
    renderer = Renderer(settings.width, settings.height)
    controller = create_controller("knife", "katana", recorder, renderer, max_seconds=1)

    # Spawn the knife orbiting effect by updating players once.
    controller._update_players(0.0)

    # The first player is team A with the knife.
    knife_owner = controller.players[0].eid

    # Kill the knife owner and advance effects once to trigger cleanup.
    controller.view.deal_damage(knife_owner, Damage(999), timestamp=0.1)
    controller._step_effects()

    # No effect should remain that still references the dead owner.
    assert all(getattr(eff, "owner", None) != knife_owner for eff in controller.effects)

