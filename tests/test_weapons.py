from __future__ import annotations

from dataclasses import dataclass, field

from app.core.types import Damage, EntityId, Vec2
from app.weapons.base import WorldView
from app.weapons.orbital import KatanaOrbital, ShurikenOrbital


@dataclass
class DummyView(WorldView):
    enemy: EntityId
    owner_pos: Vec2
    enemy_pos: Vec2
    damage_values: list[float] = field(default_factory=list)

    def get_enemy(self, owner: EntityId) -> EntityId | None:
        return self.enemy

    def get_position(self, eid: EntityId) -> Vec2:
        return self.enemy_pos if eid == self.enemy else self.owner_pos

    def get_health_ratio(self, eid: EntityId) -> float:
        return 1.0

    def deal_damage(self, eid: EntityId, damage: Damage) -> None:
        self.damage_values.append(damage.amount)

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:
        return None

    def spawn_projectile(self, *args: object, **kwargs: object) -> None:
        return None


def test_katana_orbital_hits_enemy() -> None:
    weapon = KatanaOrbital()
    owner = EntityId(1)
    enemy = EntityId(2)
    view = DummyView(enemy=enemy, owner_pos=(0.0, 0.0), enemy_pos=(60.0, 0.0))
    weapon.update(owner, view, 0.0)
    assert view.damage_values == [weapon.damage.amount]


def test_shuriken_orbital_hits_enemy() -> None:
    weapon = ShurikenOrbital()
    owner = EntityId(1)
    enemy = EntityId(2)
    view = DummyView(enemy=enemy, owner_pos=(0.0, 0.0), enemy_pos=(50.0, 0.0))
    weapon.update(owner, view, 0.0)
    assert view.damage_values == [weapon.damage.amount]
