from __future__ import annotations

from typing import Any, cast

import pytest

from app.audio.balls import BallAudio
from app.audio.engine import AudioEngine
from app.core.config import settings
from app.core.types import Damage
from app.game.controller import DASH_DAMAGE, GameController, Player
from app.game.dash import Dash
from app.render.renderer import Renderer
from app.world.entities import Ball
from app.world.physics import PhysicsWorld


def test_dash_cooldown_respected() -> None:
    dash = Dash(cooldown=1.0, duration=0.1)
    assert dash.can_dash(0.0)
    dash.start((1.0, 0.0), 0.0)
    assert dash.is_dashing
    dash.update(0.15)
    assert not dash.can_dash(0.5)
    dash.update(1.01)
    assert dash.can_dash(1.01)


def test_dash_velocity_and_invulnerability() -> None:
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
    assert dash.invulnerable_until > 0.0


def test_dash_invulnerability_expires() -> None:
    world = PhysicsWorld()
    ball = Ball.spawn(world, (0.0, 0.0))
    dash = Dash(duration=0.1, cooldown=1.0)
    damage = Damage(10.0)
    dash.start((1.0, 0.0), 0.0)
    dash.update(0.0)
    now = 0.05
    if not (dash.is_dashing or now < dash.invulnerable_until):
        ball.take_damage(damage)
    assert ball.health == ball.stats.max_health
    later = dash.invulnerable_until + 0.01
    dash.update(later)
    if not (dash.is_dashing or later < dash.invulnerable_until):
        ball.take_damage(damage)
    assert ball.health == ball.stats.max_health - damage.amount


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


def test_dash_collision_deals_damage_and_pushes() -> None:
    world = PhysicsWorld()
    ball_a = Ball.spawn(world, (0.0, 0.0))
    ball_b = Ball.spawn(world, (60.0, 0.0))

    class DummyRenderer:
        def add_impact(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            return None

        def trigger_blink(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            return None

        def trigger_hit_flash(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            return None

    class DummyEngine:
        def play_variation(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            return None

    renderer = cast(Renderer, DummyRenderer())
    engine = cast(AudioEngine, DummyEngine())
    players = [
        Player(
            ball_a.eid,
            ball_a,
            cast(Any, object()),
            cast(Any, object()),
            (1.0, 0.0),
            (0, 0, 0),
            BallAudio(engine=engine),
        ),
        Player(
            ball_b.eid,
            ball_b,
            cast(Any, object()),
            cast(Any, object()),
            (-1.0, 0.0),
            (0, 0, 0),
            BallAudio(engine=engine),
        ),
    ]
    controller = GameController(
        "katana",
        "katana",
        players,
        world,
        renderer,
        cast(Any, object()),
        engine,
        cast(Any, object()),
        cast(Any, object()),
    )
    now = 0.0
    players[0].dash.start((1.0, 0.0), now)
    controller._handle_dash_collisions(now)
    assert players[1].ball.health == players[1].ball.stats.max_health - DASH_DAMAGE.amount
    assert players[1].ball.body.velocity.x > 0.0
