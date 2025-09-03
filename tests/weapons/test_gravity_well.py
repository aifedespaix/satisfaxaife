from __future__ import annotations

from dataclasses import dataclass, field

from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import Weapon, WeaponEffect, WorldView
from app.weapons.parry import ParryEffect
from app.weapons.effects import GravityWellEffect


@dataclass
class DummyView(WorldView):
    positions: dict[EntityId, Vec2]
    impulses: dict[EntityId, Vec2] = field(default_factory=dict)
    damage: dict[EntityId, float] = field(default_factory=dict)
    weapons: dict[EntityId, Weapon] = field(default_factory=dict)
    parries: dict[EntityId, ParryEffect] = field(default_factory=dict)

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # pragma: no cover - unused
        return None

    def get_position(self, eid: EntityId) -> Vec2:
        return self.positions[eid]

    def get_velocity(self, eid: EntityId) -> Vec2:  # pragma: no cover - unused
        return (0.0, 0.0)

    def get_health_ratio(self, eid: EntityId) -> float:  # pragma: no cover - unused
        return 1.0

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:
        self.damage[eid] = self.damage.get(eid, 0.0) + damage.amount

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:
        self.impulses[eid] = (vx, vy)

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # pragma: no cover - unused
        return None

    def spawn_effect(self, effect: WeaponEffect) -> None:  # pragma: no cover - unused
        return None

    def spawn_projectile(self, *args: object, **kwargs: object) -> WeaponEffect:  # pragma: no cover - unused
        raise NotImplementedError

    def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:  # pragma: no cover - unused
        return []

    def get_weapon(self, eid: EntityId) -> Weapon:  # pragma: no cover - unused
        return self.weapons[eid]

    def get_parry(self, eid: EntityId) -> ParryEffect | None:  # pragma: no cover - unused
        return self.parries.get(eid)


def test_gravity_well_attracts_target() -> None:
    owner = EntityId(1)
    target = EntityId(2)
    view = DummyView({owner: (0.0, 0.0), target: (10.0, 0.0)})
    well = GravityWellEffect(
        owner=owner,
        position=(0.0, 0.0),
        radius=20.0,
        pull_strength=100.0,
        damage_per_second=0.0,
        ttl=1.0,
    )
    assert well.collides(view, view.get_position(target), 1.0) is True
    well.on_hit(view, target, timestamp=0.0)
    assert view.impulses[target][0] == -100.0
    assert view.impulses[target][1] == 0.0


def test_gravity_well_lifetime() -> None:
    well = GravityWellEffect(
        owner=EntityId(1),
        position=(0.0, 0.0),
        radius=10.0,
        pull_strength=0.0,
        damage_per_second=0.0,
        ttl=1.0,
    )
    assert well.step(0.5) is True
    assert well.step(0.5) is False


def test_gravity_well_damage_over_time() -> None:
    owner = EntityId(1)
    target = EntityId(2)
    view = DummyView({owner: (0.0, 0.0), target: (5.0, 0.0)})
    well = GravityWellEffect(
        owner=owner,
        position=(0.0, 0.0),
        radius=20.0,
        pull_strength=0.0,
        damage_per_second=10.0,
        ttl=1.0,
    )
    well.on_hit(view, target, timestamp=0.0)
    well.on_hit(view, target, timestamp=0.5)
    well.on_hit(view, target, timestamp=1.0)
    assert view.damage[target] == 10.0
