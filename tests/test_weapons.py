from __future__ import annotations

from dataclasses import dataclass

from app.core.types import Damage, EntityId, Vec2
from app.weapons.base import WorldView
from app.weapons.katana import Katana


@dataclass
class DummyView(WorldView):
    enemy: EntityId
    enemy_pos: Vec2
    damage_calls: int = 0

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.enemy

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.enemy_pos if eid == self.enemy else (0.0, 0.0)

    def deal_damage(self, eid: EntityId, damage: Damage) -> None:  # noqa: D401
        self.damage_calls += 1

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
        return

    def spawn_projectile(self, *args, **kwargs) -> None:  # noqa: D401, ANN002
        return


def test_katana_cooldown() -> None:
    weapon = Katana()
    view = DummyView(enemy=EntityId(2), enemy_pos=(10.0, 0.0))
    weapon.trigger(EntityId(1), view, (1.0, 0.0))
    weapon.trigger(EntityId(1), view, (1.0, 0.0))
    assert view.damage_calls == 1
    weapon.step(0.6)
    weapon.trigger(EntityId(1), view, (1.0, 0.0))
    assert view.damage_calls == 2
