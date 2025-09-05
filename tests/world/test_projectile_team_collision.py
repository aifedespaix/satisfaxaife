from __future__ import annotations

from typing import Any, cast

from app.core.types import Damage, TeamId
from app.game.controller import Player, _MatchView
from app.world.entities import Ball
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


def _make_player(world: PhysicsWorld, x: float, team: int) -> Player:
    ball = Ball.spawn(world, (x, 0.0))
    return Player(
        ball.eid,
        ball,
        cast(Any, object()),
        cast(Any, object()),
        (1.0, 0.0),
        (0, 0, 0),
        TeamId(team),
        cast(Any, object()),
    )


def test_projectile_ignores_allied_ball() -> None:
    world = PhysicsWorld()
    player_a = _make_player(world, 0.0, team=0)
    player_b = _make_player(world, 0.0, team=0)
    projectile = Projectile.spawn(
        world,
        player_a.eid,
        (0.0, 0.0),
        (0.0, 0.0),
        10.0,
        Damage(5.0),
        0.0,
        1.0,
    )
    view = _MatchView([player_a, player_b], [projectile], world, cast(Any, object()), cast(Any, object()))
    handled = world._handle_projectile_ball(projectile, projectile.shape, player_b.ball.shape, view)
    assert handled is False
    assert player_b.ball.health == player_b.ball.stats.max_health
