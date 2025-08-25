from __future__ import annotations

from dataclasses import dataclass

from app.ai.policy import SimplePolicy
from app.core.types import Damage, EntityId, Vec2
from app.weapons.base import WorldView


@dataclass
class DummyView(WorldView):
    me: EntityId
    enemy: EntityId
    pos_me: Vec2
    pos_enemy: Vec2

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.enemy

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.pos_me if eid == self.me else self.pos_enemy

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
