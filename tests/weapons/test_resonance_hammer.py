from __future__ import annotations

# ruff: noqa: E402, I001

import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if "app" in sys.modules:
    del sys.modules["app"]

from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import WeaponEffect, WorldView
from app.weapons.effects import ResonanceWaveEffect


@dataclass
class DummyView(WorldView):
    positions: dict[EntityId, Vec2]
    damage: dict[EntityId, float] = field(default_factory=dict)

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

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # pragma: no cover - unused
        return None

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # pragma: no cover - unused
        return None

    def spawn_effect(self, effect: WeaponEffect) -> None:  # pragma: no cover - unused
        return None

    def spawn_projectile(self, *args: object, **kwargs: object) -> WeaponEffect:  # pragma: no cover - unused
        raise NotImplementedError

    def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:  # pragma: no cover - unused
        return []


def test_resonance_wave_reflects_and_amplifies() -> None:
    owner = EntityId(1)
    target = EntityId(2)
    view = DummyView({owner: (0.0, 0.0), target: (5.0, 0.0)})
    wave = ResonanceWaveEffect(
        owner=owner,
        position=(0.0, 0.0),
        max_radius=10.0,
        speed=10.0,
        damage=Damage(10),
        amplification=2.0,
        thickness=1.0,
    )

    wave.step(0.5)  # expand to radius 5
    assert wave.collides(view, view.get_position(target), 0.5) is True
    wave.on_hit(view, target, timestamp=0.5)
    assert view.damage[target] == 10.0

    wave.step(0.5)  # reach max radius and reflect
    assert wave.direction == -1

    wave.step(0.5)  # contract back to radius 5
    assert wave.collides(view, view.get_position(target), 0.5) is True
    wave.on_hit(view, target, timestamp=1.5)
    assert view.damage[target] == 30.0

    assert wave.step(0.5) is False  # contract to zero and expire
