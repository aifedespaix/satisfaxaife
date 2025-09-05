from __future__ import annotations

import pygame
import pytest

from app.core.config import settings
from app.core.types import Damage, EntityId, TeamId, Vec2
from app.game.match import create_controller
from app.video.recorder import NullRecorder
from app.weapons import weapon_registry
from app.weapons.base import Weapon, WorldView


class _NoopWeapon(Weapon):
    """Weapon that never fires."""

    def __init__(self) -> None:
        super().__init__(name="noop", cooldown=0.0, damage=Damage(0))

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:  # pragma: no cover - interface
        """No-op fire method."""
        return None


def _noop_factory() -> Weapon:
    return _NoopWeapon()


_noop_factory.range_type = "contact"  # type: ignore[attr-defined]


def _register_noop_weapon() -> None:
    weapon_registry.register("noop_test", _noop_factory)


def _unregister_noop_weapon() -> None:
    weapon_registry._factories.pop("noop_test", None)


def test_match_2v2_heal_and_victory(monkeypatch: pytest.MonkeyPatch) -> None:
    """2v2 matches spawn players correctly and handle ally collisions."""

    monkeypatch.setattr(settings, "team_a_count", 2)
    monkeypatch.setattr(settings, "team_b_count", 2)
    _register_noop_weapon()

    try:
        controller = create_controller("noop_test", "noop_test", NullRecorder(), renderer=None, max_seconds=1)
        assert len(controller.players) == 4

        step = settings.height / 3.0
        expected_y = [step, step * 2]

        for idx, player in enumerate(controller.players[:2]):
            assert player.ball.body.position.x == pytest.approx(settings.width * 0.25)
            assert player.ball.body.position.y == pytest.approx(expected_y[idx])

        for idx, player in enumerate(controller.players[2:]):
            assert player.ball.body.position.x == pytest.approx(settings.width * 0.75)
            assert player.ball.body.position.y == pytest.approx(expected_y[idx])

        healer, target = controller.players[0], controller.players[1]
        target.ball.health = 90.0
        healer.ball.body.position = target.ball.body.position
        healer.ball.body.velocity = (healer.dash.speed, 0.0)
        healer.dash.is_dashing = True
        healer.dash._direction = (1.0, 0.0)  # type: ignore[attr-defined]

        controller._resolve_dash_collision(healer, 0.0)

        assert target.ball.health == pytest.approx(95.0)

        for foe in controller.players[2:]:
            foe.alive = False

        monkeypatch.setattr(controller, "_play_winner_sequence", lambda: None)
        monkeypatch.setattr(pygame.event, "get", lambda: [])
        controller._run_match_loop(0.0)
        assert controller.winner_team == TeamId(0)
    finally:
        _unregister_noop_weapon()


def test_match_1v2_heal_and_victory(monkeypatch: pytest.MonkeyPatch) -> None:
    """1v2 matches support asymmetric team sizes and healing."""

    monkeypatch.setattr(settings, "team_a_count", 1)
    monkeypatch.setattr(settings, "team_b_count", 2)
    _register_noop_weapon()

    try:
        controller = create_controller("noop_test", "noop_test", NullRecorder(), renderer=None, max_seconds=1)
        assert len(controller.players) == 3

        assert controller.players[0].ball.body.position.x == pytest.approx(settings.width * 0.25)
        assert controller.players[0].ball.body.position.y == pytest.approx(settings.height / 2.0)

        step = settings.height / 3.0
        expected_y = [step, step * 2]
        for idx, player in enumerate(controller.players[1:]):
            assert player.ball.body.position.x == pytest.approx(settings.width * 0.75)
            assert player.ball.body.position.y == pytest.approx(expected_y[idx])

        healer, target = controller.players[1], controller.players[2]
        target.ball.health = 90.0
        healer.ball.body.position = target.ball.body.position
        healer.ball.body.velocity = (healer.dash.speed, 0.0)
        healer.dash.is_dashing = True
        healer.dash._direction = (1.0, 0.0)  # type: ignore[attr-defined]

        controller._resolve_dash_collision(healer, 0.0)

        assert target.ball.health == pytest.approx(95.0)

        controller.players[0].alive = False
        monkeypatch.setattr(controller, "_play_winner_sequence", lambda: None)
        monkeypatch.setattr(pygame.event, "get", lambda: [])
        controller._run_match_loop(0.0)
        assert controller.winner_team == TeamId(1)
    finally:
        _unregister_noop_weapon()
