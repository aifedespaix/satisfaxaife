from __future__ import annotations

from dataclasses import dataclass, field

from app.core.types import Damage, EntityId, Vec2
from app.weapons.base import WeaponEffect, WorldView
from app.weapons.katana import Katana
from app.weapons.shuriken import Shuriken


@dataclass
class DummyView(WorldView):
    enemy: EntityId
    owner_pos: Vec2
    enemy_pos: Vec2
    damage_values: list[float] = field(default_factory=list)
    effects: list[WeaponEffect] = field(default_factory=list)

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

    def spawn_effect(self, effect: WeaponEffect) -> None:
        self.effects.append(effect)

    def spawn_projectile(self, *args: object, **kwargs: object) -> WeaponEffect:
        class _Dummy(WeaponEffect):
            owner: EntityId = EntityId(0)

            def step(self, dt: float) -> bool:
                return False

            def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:
                return False

            def on_hit(self, view: WorldView, target: EntityId) -> bool:
                return False

            def draw(self, renderer: object, view: WorldView) -> None:
                return None

            def destroy(self) -> None:
                return None

        return _Dummy()


def test_katana_hits_enemy() -> None:
    weapon = Katana()
    owner = EntityId(1)
    enemy = EntityId(2)
    view = DummyView(enemy=enemy, owner_pos=(0.0, 0.0), enemy_pos=(60.0, 0.0))
    weapon.update(owner, view, 0.0)
    assert view.effects, "Orbit effect not spawned"
    eff = view.effects[0]
    if eff.collides(view, view.enemy_pos, 1.0):
        eff.on_hit(view, enemy)
    assert view.damage_values == [weapon.damage.amount]


def test_shuriken_projectile_spawns() -> None:
    weapon = Shuriken()
    owner = EntityId(1)
    enemy = EntityId(2)
    view = DummyView(enemy=enemy, owner_pos=(0.0, 0.0), enemy_pos=(0.0, 0.0))
    weapon._fire(owner, view, (1.0, 0.0))
    assert not view.damage_values
