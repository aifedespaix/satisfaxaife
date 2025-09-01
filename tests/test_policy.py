from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pytest

from app.ai.policy import SimplePolicy, policy_for_weapon
from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import WeaponEffect, WorldView
from app.weapons.shuriken import Shuriken


@dataclass
class DummyView(WorldView):
    me: EntityId
    enemy: EntityId
    pos_me: Vec2
    pos_enemy: Vec2
    vel_me: Vec2 = (0.0, 0.0)
    vel_enemy: Vec2 = (0.0, 0.0)
    health_me: float = 1.0
    health_enemy: float = 1.0
    last_velocity: Vec2 | None = field(default=None, init=False)

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.enemy

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.pos_me if eid == self.me else self.pos_enemy

    def get_velocity(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.vel_me if eid == self.me else self.vel_enemy

    def get_health_ratio(self, eid: EntityId) -> float:  # noqa: D401
        return self.health_me if eid == self.me else self.health_enemy

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:  # noqa: D401
        return

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
        return

    def spawn_effect(self, effect: WeaponEffect) -> None:  # noqa: D401
        return

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # noqa: D401
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
        sprite: object | None = None,
        spin: float = 0.0,
        trail_color: tuple[int, int, int] | None = None,
        acceleration: float = 0.0,
    ) -> WeaponEffect:  # noqa: D401
        self.last_velocity = velocity

        class _Dummy(WeaponEffect):
            owner: EntityId = owner

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


def test_kiter_moves_away() -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (50.0, 0.0))
    policy = SimplePolicy("kiter")
    accel, face, fire = policy.decide(EntityId(1), view, 600.0)
    assert accel[0] < 0  # moves left, away from enemy
    assert fire is True


def test_kiter_closes_distance_when_out_of_range() -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (600.0, 0.0))
    policy = SimplePolicy("kiter")
    accel, _, fire = policy.decide(EntityId(1), view, 600.0)
    assert accel[0] > 0  # moves right, toward enemy
    assert fire is False


def test_evader_always_moves_away() -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (600.0, 0.0))
    policy = SimplePolicy("evader")
    accel, _, fire = policy.decide(EntityId(1), view, 600.0)
    assert accel[0] < 0  # continues to flee
    assert fire is False


def test_evader_fires_when_far_enough() -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (800.0, 0.0))
    policy = SimplePolicy("evader")
    accel, _, fire = policy.decide(EntityId(1), view, 600.0)
    assert accel[0] < 0  # still moving away
    assert fire is True


def test_kiter_leads_moving_target() -> None:
    view = DummyView(
        EntityId(1),
        EntityId(2),
        (0.0, 0.0),
        (0.0, 100.0),
        vel_enemy=(100.0, 0.0),
    )
    policy = SimplePolicy("kiter")
    _, face, _ = policy.decide(EntityId(1), view, 300.0)
    assert face[0] > 0  # aims ahead of the moving target


@pytest.mark.parametrize("style", ["aggressive", "kiter", "evader"])
def test_retreats_on_low_health(style: Literal["aggressive", "kiter", "evader"]) -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (50.0, 0.0), health_me=0.1)
    policy = SimplePolicy(style)
    accel, face, fire = policy.decide(EntityId(1), view, 600.0)
    assert accel[0] < 0  # retreats from enemy
    assert face == (1.0, 0.0)  # still faces enemy
    assert fire is True


@pytest.mark.parametrize("style", ["aggressive", "kiter", "evader"])
def test_low_health_fire_requires_range(style: Literal["aggressive", "kiter", "evader"]) -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (600.0, 0.0), health_me=0.1)
    policy = SimplePolicy(style)
    _, _, fire = policy.decide(EntityId(1), view, 600.0)
    assert fire is False


@pytest.mark.parametrize("style", ["aggressive", "kiter", "evader"])
def test_both_low_health_engage(style: Literal["aggressive", "kiter", "evader"]) -> None:
    view = DummyView(
        EntityId(1),
        EntityId(2),
        (0.0, 0.0),
        (50.0, 0.0),
        health_me=0.1,
        health_enemy=0.1,
    )
    policy = SimplePolicy(style)
    accel, _, fire = policy.decide(EntityId(1), view, 600.0)
    assert accel[0] > 0  # moves toward enemy
    assert fire is True


def test_horizontal_alignment_has_vertical_component() -> None:
    me = EntityId(1)
    enemy = EntityId(2)
    view = DummyView(me, enemy, (0.0, 0.0), (50.0, 0.0))
    policy = SimplePolicy("aggressive")
    weapon = Shuriken()
    accel, face, fire = policy.decide(me, view, 600.0)
    assert fire is True
    assert face[1] != 0.0
    weapon.trigger(me, view, face)
    assert view.last_velocity is not None
    assert view.last_velocity[1] != 0.0


def test_aggressive_dodges_projectiles() -> None:
    me = EntityId(1)
    enemy = EntityId(2)

    @dataclass
    class ViewWithProjectile(DummyView):
        proj_pos: Vec2 = (0.0, 0.0)
        proj_vel: Vec2 = (0.0, 0.0)

        def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:  # noqa: D401
            return [ProjectileInfo(owner=enemy, position=self.proj_pos, velocity=self.proj_vel)]

    view = ViewWithProjectile(
        me, enemy, (0.0, 0.0), (100.0, 0.0), proj_pos=(40.0, 0.0), proj_vel=(-100.0, 0.0)
    )
    policy = SimplePolicy("aggressive")
    accel, _, _ = policy.decide(me, view, 600.0)
    assert accel[1] < 0  # dodges downward


def test_evader_dodges_projectiles() -> None:
    me = EntityId(1)
    enemy = EntityId(2)

    @dataclass
    class ViewWithProjectile(DummyView):
        proj_pos: Vec2 = (0.0, 0.0)
        proj_vel: Vec2 = (0.0, 0.0)

        def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:  # noqa: D401
            return [ProjectileInfo(owner=enemy, position=self.proj_pos, velocity=self.proj_vel)]

    view = ViewWithProjectile(
        me, enemy, (0.0, 0.0), (100.0, 0.0), proj_pos=(40.0, 0.0), proj_vel=(-100.0, 0.0)
    )
    policy = SimplePolicy("evader")
    accel, _, _ = policy.decide(me, view, 600.0)
    assert accel[1] < 0  # dodges downward


def test_policy_for_bazooka_is_evader() -> None:
    policy = policy_for_weapon("bazooka")
    assert policy.style == "evader"
    assert policy.desired_dist_factor > 1.0


def test_policy_for_knife_prioritises_dodging() -> None:
    policy = policy_for_weapon("knife")
    assert policy.style == "aggressive"
    assert policy.dodge_bias > 0.5
