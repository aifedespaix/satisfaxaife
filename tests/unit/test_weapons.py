from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, cast

import pytest

from app.core.config import settings
from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.game.match import MatchTimeout, run_match
from app.render.renderer import Renderer
from app.video.recorder import NullRecorder
from app.weapons import weapon_registry
from app.weapons.base import Weapon, WeaponEffect, WorldView
from app.weapons.bazooka import Bazooka
from app.weapons.katana import Katana
from app.weapons.knife import Knife
from app.weapons.shuriken import Shuriken


@dataclass
class DummyView(WorldView):
    enemy: EntityId
    enemy_pos: Vec2
    enemy_vel: Vec2 = (0.0, 0.0)
    damage_values: list[float] = field(default_factory=list)
    speed_bonus: dict[EntityId, float] = field(default_factory=dict)
    effects: list[WeaponEffect] = field(default_factory=list)
    projectiles: list[dict[str, object]] = field(default_factory=list)

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.enemy

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.enemy_pos if eid == self.enemy else (0.0, 0.0)

    def get_velocity(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.enemy_vel if eid == self.enemy else (0.0, 0.0)

    def get_health_ratio(self, eid: EntityId) -> float:  # noqa: D401
        return 1.0

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:  # noqa: D401
        self.damage_values.append(damage.amount)

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
        return

    def spawn_effect(self, effect: WeaponEffect) -> None:  # noqa: D401
        self.effects.append(effect)

    def spawn_projectile(
        self,
        owner: EntityId,
        position: Vec2,
        velocity: Vec2,
        radius: float,
        damage: Damage,
        knockback: float,
        ttl: float,
        sprite: object | None = None,
        spin: float = 0.0,
        trail_color: tuple[int, int, int] | None = None,
        acceleration: float = 0.0,
    ) -> WeaponEffect:  # noqa: D401,E501
        self.projectiles.append(
            {
                "owner": owner,
                "position": position,
                "velocity": velocity,
                "radius": radius,
                "damage": damage,
                "ttl": ttl,
                "trail_color": trail_color,
                "acceleration": acceleration,
            }
        )

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
    knife = Knife()

    assert katana.speed == 5.0
    assert shuriken.speed == 600.0
    assert knife.speed == 12.0


def test_knife_applies_speed_bonus() -> None:
    view = DummyView(enemy=EntityId(2), enemy_pos=(0.0, 0.0))
    knife = Knife()
    knife.update(EntityId(1), view, 0.0)
    assert view.speed_bonus[EntityId(1)] == knife.player_speed_bonus
    assert knife.player_speed_bonus == 120.0
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
    vx, vy = cast(Vec2, projectile["velocity"])
    assert vx == pytest.approx(bazooka.speed)
    assert vy == pytest.approx(0.0)
    assert projectile["radius"] == bazooka.missile_radius
    assert math.isinf(cast(float, projectile["ttl"]))
    assert projectile["trail_color"] == (255, 200, 50)
    effect = view.effects[0]
    assert effect.collides(view, (0.0, 0.0), 1.0) is False


def test_bazooka_leads_moving_target() -> None:
    view = DummyView(
        enemy=EntityId(2),
        enemy_pos=(300.0, 0.0),
        enemy_vel=(0.0, 100.0),
    )
    bazooka = Bazooka()
    bazooka.update(EntityId(1), view, 0.0)
    projectile = view.projectiles[0]
    vx, vy = cast(Vec2, projectile["velocity"])
    distance = math.hypot(300.0, 0.0)
    time_to_target = distance / bazooka.speed
    predicted_y = 0.0 + 100.0 * time_to_target
    norm = math.hypot(300.0, predicted_y)
    expected_vx = bazooka.speed * 300.0 / norm
    expected_vy = bazooka.speed * predicted_y / norm
    assert vx == pytest.approx(expected_vx)
    assert vy == pytest.approx(expected_vy)


@dataclass
class _OrientView(WorldView):
    enemy: EntityId
    enemy_pos: Vec2
    effects: list[WeaponEffect] = field(default_factory=list)
    projectile: object | None = None

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.enemy

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.enemy_pos if eid == self.enemy else (0.0, 0.0)

    def get_velocity(self, eid: EntityId) -> Vec2:  # noqa: D401
        return (0.0, 0.0)

    def get_health_ratio(self, eid: EntityId) -> float:  # noqa: D401
        return 1.0

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:  # noqa: D401
        return None

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
        return None

    def spawn_effect(self, effect: WeaponEffect) -> None:  # noqa: D401
        self.effects.append(effect)

    def spawn_projectile(
        self,
        owner: EntityId,
        position: Vec2,
        velocity: Vec2,
        radius: float,
        damage: Damage,
        knockback: float,
        ttl: float,
        sprite: object | None = None,
        spin: float = 0.0,
        trail_color: tuple[int, int, int] | None = None,
        acceleration: float = 0.0,
    ) -> WeaponEffect:  # noqa: D401
        class _Dummy(WeaponEffect):
            owner: EntityId = owner
            angle: float = 0.0

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

        proj = _Dummy()
        self.projectile = proj
        return proj

    def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:  # noqa: D401
        return []

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # noqa: D401
        return None


def test_bazooka_sprite_and_projectile_orientation() -> None:
    view = _OrientView(enemy=EntityId(2), enemy_pos=(100.0, 100.0))
    bazooka = Bazooka()
    bazooka.update(EntityId(1), view, 0.0)
    assert view.projectile is not None
    assert len(view.effects) == 1
    effect = cast(Any, view.effects[0])
    dx, dy = 100.0, 100.0
    expected_weapon_angle = math.atan2(dy, dx)
    expected_projectile_angle = math.atan2(dy, dx) + math.pi / 2
    assert effect.angle == pytest.approx(expected_weapon_angle)
    proj = cast(Any, view.projectile)
    assert proj.angle == pytest.approx(expected_projectile_angle)


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
