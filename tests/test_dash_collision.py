from __future__ import annotations

from app.core.types import Damage
from tests.helpers import make_controller, make_player


def test_dash_collision_deals_damage_and_knockback() -> None:
    player_a = make_player(1, 0.0, team=0)
    player_b = make_player(2, 70.0, team=1)
    controller = make_controller(player_a, player_b)
    player_a.dash.start((1.0, 0.0), 0.0)
    controller._update_players(0.0)
    controller._resolve_dash_collision(player_a, 0.0)
    assert player_b.ball.health == 95.0
    assert player_b.ball.body.velocity.x > 0.0
    assert player_a.dash.has_hit


def test_dash_damage_scales_with_speed() -> None:
    player_a = make_player(1, 0.0, team=0)
    player_b = make_player(2, 70.0, team=1)
    controller = make_controller(player_a, player_b)
    player_a.dash.start((1.0, 0.0), 0.0)
    player_a.ball.body.velocity = (player_a.dash.speed / 2.0, 0.0)
    controller._resolve_dash_collision(player_a, 0.0)
    assert player_b.ball.health == 97.5


def test_dashing_player_can_be_damaged() -> None:
    player_a = make_player(1, 0.0, team=0)
    player_b = make_player(2, 200.0, team=1)
    controller = make_controller(player_a, player_b)
    player_a.dash.start((1.0, 0.0), 0.0)
    controller.view.deal_damage(player_a.eid, Damage(10.0), 0.0)
    assert player_a.ball.health == 90.0
