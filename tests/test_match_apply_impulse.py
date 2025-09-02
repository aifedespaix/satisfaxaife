from __future__ import annotations

from typing import Any, cast

import pytest

from app.core.types import EntityId
from app.game.match import Player, _MatchView
from app.world.entities import Ball
from app.world.physics import PhysicsWorld


def test_apply_impulse_raises_for_unknown_entity() -> None:
    world = PhysicsWorld()
    ball = Ball.spawn(world, (0.0, 0.0))
    player = Player(
        eid=ball.eid,
        ball=ball,
        weapon=cast(Any, object()),
        policy=cast(Any, object()),
        face=(1.0, 0.0),
        color=(255, 255, 255),
        audio=cast(Any, object()),
    )
    view = _MatchView([player], [], world, cast(Any, object()), cast(Any, object()))

    with pytest.raises(KeyError):
        view.apply_impulse(EntityId(ball.eid.value + 1), 1.0, 0.0)
