from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

import pytest

from app.core.config import settings
from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.game.match import MatchTimeout, run_match
from app.render.renderer import Renderer
from app.video.recorder import NullRecorder, Recorder
from app.weapons import weapon_registry
from app.weapons.base import Weapon, WeaponEffect, WorldView
from app.weapons.katana import Katana
from app.weapons.shuriken import Shuriken


@dataclass
class DummyView(WorldView):
    enemy: EntityId
    enemy_pos: Vec2
    damage_values: list[float] = field(default_factory=list)

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.enemy

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.enemy_pos if eid == self.enemy else (0.0, 0.0)

    def get_velocity(self, eid: EntityId) -> Vec2:  # noqa: D401
        return (0.0, 0.0)

    def get_health_ratio(self, eid: EntityId) -> float:  # noqa: D401
        return 1.0

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:  # noqa: D401
        self.damage_values.append(damage.amount)

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
        return

    def spawn_effect(self, effect: WeaponEffect) -> None:  # noqa: D401
        return

    def spawn_projectile(self, *args: object, **kwargs: object) -> WeaponEffect:  # noqa: D401
        class _Dummy(WeaponEffect):
            owner: EntityId = EntityId(0)

            def step(self, dt: float) -> bool:
                return False

            def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:
                return False

            def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool:
                return False

            def draw(self, renderer: object, view: WorldView) -> None:
                return None

            def destroy(self) -> None:
                return None

        return _Dummy()

    def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:  # noqa: D401
        return []


def test_weapon_speed_attribute() -> None:
    """Weapons expose their projectile speed on the base class."""
    katana = Katana()
    shuriken = Shuriken()

    assert katana.speed == 0.0
    assert shuriken.speed == 600.0


class SpyWeapon(Weapon):
    """Weapon used to verify update calls inside the match loop."""

    calls: list[EntityId] = []

    def __init__(self) -> None:
        super().__init__(name="spy", cooldown=0.0, damage=Damage(0))

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:  # noqa: D401
        return None

    def update(self, owner: EntityId, view: WorldView, dt: float) -> None:  # noqa: D401
        self.calls.append(owner)


def test_weapon_update_called_each_frame() -> None:
    SpyWeapon.calls = []
    if "spy" not in weapon_registry.names():
        weapon_registry.register("spy", SpyWeapon)
    recorder = cast(Recorder, NullRecorder())
    renderer = Renderer(settings.width, settings.height)
    with pytest.raises(MatchTimeout):
        run_match("spy", "spy", recorder, renderer, max_seconds=1)
    assert set(SpyWeapon.calls) == {EntityId(1), EntityId(2)}
