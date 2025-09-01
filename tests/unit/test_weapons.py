from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from app.core.config import settings
from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.game.match import MatchTimeout, run_match
from app.render.renderer import Renderer
from app.video.recorder import NullRecorder
from app.weapons import weapon_registry
from app.weapons.base import Weapon, WeaponEffect, WorldView
from app.weapons.katana import Katana
from app.weapons.shuriken import Shuriken
from app.weapons.knife import Knife
from app.weapons.bazooka import Bazooka


@dataclass
class DummyView(WorldView):
    enemy: EntityId
    enemy_pos: Vec2
    damage_values: list[float] = field(default_factory=list)
    speed_bonus: dict[EntityId, float] = field(default_factory=dict)
    effects: list[WeaponEffect] = field(default_factory=list)
    projectiles: list[dict[str, object]] = field(default_factory=list)

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
        self.effects.append(effect)

    def spawn_projectile(self, owner: EntityId, position: Vec2, velocity: Vec2, radius: float, damage: Damage, knockback: float, ttl: float, sprite: object | None = None, spin: float = 0.0) -> WeaponEffect:  # noqa: D401,E501
        self.projectiles.append({
            "owner": owner,
            "position": position,
            "velocity": velocity,
            "radius": radius,
            "damage": damage,
            "ttl": ttl,
        })

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

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # noqa: D401
        self.speed_bonus[eid] = self.speed_bonus.get(eid, 0.0) + bonus


def test_weapon_speed_attribute() -> None:
    """Weapons expose their projectile speed on the base class."""
    katana = Katana()
    shuriken = Shuriken()

    assert katana.speed == 5.0
    assert shuriken.speed == 600.0


def test_knife_applies_speed_bonus() -> None:
    view = DummyView(enemy=EntityId(2), enemy_pos=(0.0, 0.0))
    knife = Knife()
    knife.update(EntityId(1), view, 0.0)
    assert view.speed_bonus[EntityId(1)] == knife.player_speed_bonus
    assert len(view.effects) == 1


def test_knife_damage_value() -> None:
    """Knife base damage should reflect its lighter attack power."""
    knife = Knife()
    assert knife.damage.amount == 8


def test_bazooka_fires_missile() -> None:
    view = DummyView(enemy=EntityId(2), enemy_pos=(100.0, 0.0))
    bazooka = Bazooka()
    bazooka.update(EntityId(1), view, 0.0)
    assert len(view.projectiles) == 1
    projectile = view.projectiles[0]
    vx, vy = projectile["velocity"]
    assert vx == pytest.approx(bazooka.speed)
    assert vy == pytest.approx(0.0)
    assert projectile["radius"] == bazooka.missile_radius
    effect = view.effects[0]
    assert effect.collides(view, (0.0, 0.0), 1.0) is False


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
    recorder = NullRecorder()
    renderer = Renderer(settings.width, settings.height)
    with pytest.raises(MatchTimeout):
        run_match("spy", "spy", recorder, renderer, max_seconds=1)
    assert set(SpyWeapon.calls) == {EntityId(1), EntityId(2)}
