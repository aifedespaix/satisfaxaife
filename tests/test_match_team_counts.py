from __future__ import annotations

from typing import Any

import pytest

from app.core.config import settings
from app.core.types import Damage, EntityId, Vec2
from app.game.match import create_controller
from app.video.recorder import NullRecorder
from app.weapons import weapon_registry
from app.weapons.base import Weapon, WorldView


class _NoopWeapon(Weapon):
    """Weapon that never fires."""

    def __init__(self) -> None:
        super().__init__(name="noop", cooldown=0.0, damage=Damage(0))

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:  # noqa: D401 - interface requirement
        """No-op fire method."""


def _noop_factory() -> Weapon:
    return _NoopWeapon()


_noop_factory.range_type = "contact"  # type: ignore[attr-defined]


def test_create_controller_respects_team_counts(monkeypatch: Any) -> None:
    """Players are spawned according to configured team sizes."""

    monkeypatch.setattr(settings, "team_a_count", 2)
    monkeypatch.setattr(settings, "team_b_count", 2)

    weapon_registry.register("noop_test", _noop_factory)

    controller = create_controller(
        "noop_test",
        "noop_test",
        NullRecorder(),
        renderer=None,
        max_seconds=1,
    )

    try:
        assert len(controller.players) == 4

        step = settings.height / 3.0
        expected_y = [step, step * 2]

        for idx, player in enumerate(controller.players[:2]):
            assert player.ball.body.position.x == pytest.approx(settings.width * 0.25)
            assert player.ball.body.position.y == pytest.approx(expected_y[idx])

        for idx, player in enumerate(controller.players[2:]):
            assert player.ball.body.position.x == pytest.approx(settings.width * 0.75)
            assert player.ball.body.position.y == pytest.approx(expected_y[idx])
    finally:
        weapon_registry._factories.pop("noop_test", None)

