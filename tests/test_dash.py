from __future__ import annotations

import pytest

from app.core.config import settings
from app.game.dash import Dash
from app.render.renderer import Renderer
from app.world.entities import Ball
from app.world.physics import PhysicsWorld


def test_dash_unique_damage_instance() -> None:
    dash_a = Dash()
    dash_b = Dash()
    assert dash_a.damage.amount == 5.0
    assert dash_b.damage.amount == 5.0
    assert dash_a.damage is not dash_b.damage


def test_dash_cooldown_respected() -> None:
    dash = Dash(cooldown=1.0, duration=0.1)
    assert dash.can_dash(0.0)
    dash.start((1.0, 0.0), 0.0)
    assert dash.is_dashing
    dash.update(0.15)
    assert not dash.can_dash(0.5)
    dash.update(1.01)
    assert dash.can_dash(1.01)


def test_dash_applies_velocity() -> None:
    world = PhysicsWorld()
    ball = Ball.spawn(world, (0.0, 0.0))
    dash = Dash(speed=500.0, duration=0.2, cooldown=1.0)
    dash.start((1.0, 0.0), 0.0)
    dash.update(0.0)
    if dash.is_dashing:
        ball.body.velocity = (
            dash.direction[0] * dash.speed,
            dash.direction[1] * dash.speed,
        )
    velocity = ball.body.velocity
    assert velocity.x == pytest.approx(500.0)
    assert velocity.y == pytest.approx(0.0)


def test_dash_trail_amplified() -> None:
    renderer = Renderer(display=False)
    team_color = settings.theme.team_a.primary
    pos_a = (0.0, 0.0)
    pos_b = (10.0, 0.0)
    radius = 5

    renderer.draw_ball(pos_a, radius, settings.ball_color, team_color)
    renderer.draw_ball(pos_b, radius, settings.ball_color, team_color)
    normal_len = len(renderer._get_state(team_color).trail)

    renderer_dash = Renderer(display=False)
    renderer_dash.draw_ball(pos_a, radius, settings.ball_color, team_color)
    renderer_dash.draw_ball(pos_b, radius, settings.ball_color, team_color, is_dashing=True)
    dash_len = len(renderer_dash._get_state(team_color).trail)

    assert dash_len > normal_len


def test_dash_generates_ghosts() -> None:
    renderer = Renderer(display=False)
    team_color = settings.theme.team_a.primary
    pos_a = (0.0, 0.0)
    pos_b = (10.0, 0.0)
    radius = 5

    renderer.draw_ball(pos_a, radius, settings.ball_color, team_color, is_dashing=True)
    renderer.draw_ball(pos_b, radius, settings.ball_color, team_color, is_dashing=True)
    ghosts = renderer._get_state(team_color).ghosts
    assert len(ghosts) > 0

    for _ in range(5):
        renderer.draw_ball(pos_b, radius, settings.ball_color, team_color)

    assert not renderer._get_state(team_color).ghosts
