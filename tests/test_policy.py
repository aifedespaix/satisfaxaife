from __future__ import annotations

from dataclasses import dataclass

import pytest

from app.ai.policy import SimplePolicy
from app.core.types import Damage, EntityId, Vec2
from app.weapons.base import WorldView


@dataclass
class DummyView(WorldView):
    me: EntityId
    enemy: EntityId
    pos_me: Vec2
    pos_enemy: Vec2
    health_me: float = 1.0
    health_enemy: float = 1.0

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.enemy

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.pos_me if eid == self.me else self.pos_enemy

    def get_health_ratio(self, eid: EntityId) -> float:  # noqa: D401
        return self.health_me if eid == self.me else self.health_enemy

    def deal_damage(self, eid: EntityId, damage: Damage) -> None:  # noqa: D401
        return

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
        return

    def spawn_projectile(self, *args, **kwargs) -> None:  # noqa: D401, ANN002
        return


def test_kiter_moves_away() -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (50.0, 0.0))
    policy = SimplePolicy("kiter")
    accel, face, fire = policy.decide(EntityId(1), view)
    assert accel[0] < 0  # moves left, away from enemy
    assert fire is True


@pytest.mark.parametrize("style", ["aggressive", "kiter"])
def test_retreats_on_low_health(style: str) -> None:
    view = DummyView(
        EntityId(1), EntityId(2), (0.0, 0.0), (50.0, 0.0), health_me=0.1
    )
    policy = SimplePolicy(style)
    accel, face, fire = policy.decide(EntityId(1), view)
    assert accel[0] < 0  # retreats from enemy
    assert face == (1.0, 0.0)  # still faces enemy
    assert fire is False
