from __future__ import annotations

from dataclasses import dataclass

from app.core.types import Damage, EntityId, Vec2
from app.weapons.base import WorldView
from app.weapons.katana import Katana
from app.weapons.shuriken import Shuriken


@dataclass
class DummyView(WorldView):
    enemy: EntityId
    enemy_pos: Vec2
    position_owner: Vec2 = (0.0, 0.0)
    damage_calls: int = 0
    last_damage: Damage | None = None
    projectile_damage: Damage | None = None

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.enemy

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.enemy_pos if eid == self.enemy else self.position_owner

    def deal_damage(self, eid: EntityId, damage: Damage) -> None:  # noqa: D401
        self.damage_calls += 1
        self.last_damage = damage

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
        return

    def spawn_projectile(
        self,
        owner: EntityId,
        position: Vec2,
        velocity: Vec2,
        radius: float,
        damage: Damage,
        knockback: float,
        ttl: float,
    ) -> None:  # noqa: D401
        self.projectile_damage = damage


def test_katana_cooldown() -> None:
    weapon = Katana()
    view = DummyView(enemy=EntityId(2), enemy_pos=(10.0, 0.0))
    weapon.trigger(EntityId(1), view, (1.0, 0.0))
    weapon.trigger(EntityId(1), view, (1.0, 0.0))
    assert view.damage_calls == 1
    weapon.step(0.6)
    weapon.trigger(EntityId(1), view, (1.0, 0.0))
    assert view.damage_calls == 2


def test_weapon_damage_values() -> None:
    view = DummyView(enemy=EntityId(2), enemy_pos=(10.0, 0.0))
    katana = Katana()
    katana.trigger(EntityId(1), view, (1.0, 0.0))
    assert view.last_damage is not None
    assert view.last_damage.amount == 18

    shuriken = Shuriken()
    view_shuriken = DummyView(enemy=EntityId(2), enemy_pos=(0.0, 0.0))
    shuriken.trigger(EntityId(1), view_shuriken, (1.0, 0.0))
    assert view_shuriken.projectile_damage is not None
    assert view_shuriken.projectile_damage.amount == 10
