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


def test_get_enemy_returns_opponent_only() -> None:
    world = PhysicsWorld()
    player_a = _make_player(world, 0.0, 0)
    player_b = _make_player(world, 10.0, 1)
    view = _MatchView([player_a, player_b], [], world, cast(Any, object()), cast(Any, object()))

    assert view.get_enemy(player_a.eid) == player_b.eid
    assert view.get_enemy(player_b.eid) == player_a.eid


def test_iter_projectiles_filters_by_team() -> None:
    world = PhysicsWorld()
    player_a = _make_player(world, 0.0, 0)
    player_b = _make_player(world, 10.0, 1)
    proj_a = Projectile.spawn(world, player_a.eid, (0.0, 0.0), (1.0, 0.0), 1.0, Damage(1.0), 0.0, 1.0)
    proj_b = Projectile.spawn(world, player_b.eid, (10.0, 0.0), (1.0, 0.0), 1.0, Damage(1.0), 0.0, 1.0)
    view = _MatchView([player_a, player_b], [proj_a, proj_b], world, cast(Any, object()), cast(Any, object()))

    infos = list(view.iter_projectiles(excluding=player_a.eid))
    assert [info.owner for info in infos] == [player_b.eid]
