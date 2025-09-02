from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import pytest

from app.ai.policy import SimplePolicy, policy_for_weapon
from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import WeaponEffect, WorldView
from app.weapons.shuriken import Shuriken
from pymunk import Vec2 as Vec2d


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
    last_velocity: Vec2d | None = field(default=None, init=False)

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
        self.last_velocity = Vec2d(*velocity)

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
    accel, face, fire, parry = policy.decide(EntityId(1), view, 600.0)
    assert accel[0] < 0  # moves left, away from enemy
    assert fire is True
    assert parry is False


def test_kiter_closes_distance_when_out_of_range() -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (600.0, 0.0))
    policy = SimplePolicy("kiter")
    accel, _, fire, parry = policy.decide(EntityId(1), view, 600.0)
    assert accel[0] > 0  # moves right, toward enemy
    assert fire is False
    assert parry is False


def test_evader_always_moves_away() -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (600.0, 0.0))
    policy = SimplePolicy("evader")
    accel, _, fire, parry = policy.decide(EntityId(1), view, 600.0)
    assert accel[0] < 0  # continues to flee
    assert fire is False
    assert parry is False


def test_evader_fires_when_far_enough() -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (800.0, 0.0))
    policy = SimplePolicy("evader")
    accel, _, fire, parry = policy.decide(EntityId(1), view, 600.0)
    assert accel[0] < 0  # still moving away
    assert fire is True
    assert parry is False


def test_kiter_leads_moving_target() -> None:
    view = DummyView(
        EntityId(1),
        EntityId(2),
        (0.0, 0.0),
        (0.0, 100.0),
        vel_enemy=(100.0, 0.0),
    )
    policy = SimplePolicy("kiter")
    _, face, _, parry = policy.decide(EntityId(1), view, 300.0)
    assert face[0] > 0  # aims ahead of the moving target
    assert parry is False


@pytest.mark.parametrize("style", ["aggressive", "kiter", "evader"])
def test_retreats_on_low_health(style: Literal["aggressive", "kiter", "evader"]) -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (50.0, 0.0), health_me=0.1)
    policy = SimplePolicy(style)
    accel, face, fire, parry = policy.decide(EntityId(1), view, 600.0)
    assert accel[0] < 0  # retreats from enemy
    assert face[0] > 0  # still faces enemy horizontally
    assert fire is True
    assert parry is False


@pytest.mark.parametrize("style", ["aggressive", "kiter", "evader"])
def test_low_health_fire_requires_range(style: Literal["aggressive", "kiter", "evader"]) -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (600.0, 0.0), health_me=0.1)
    policy = SimplePolicy(style)
    _, _, fire, parry = policy.decide(EntityId(1), view, 600.0)
    assert fire is False
    assert parry is False


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
    accel, _, fire, parry = policy.decide(EntityId(1), view, 600.0)
    assert accel[0] > 0  # moves toward enemy
    assert fire is True
    assert parry is False


def test_horizontal_alignment_has_vertical_component() -> None:
    me = EntityId(1)
    enemy = EntityId(2)
    view = DummyView(me, enemy, (0.0, 0.0), (50.0, 0.0))
    policy = SimplePolicy("aggressive")
    weapon = Shuriken()
    accel, face, fire, parry = policy.decide(me, view, 600.0)
    assert fire is True
    assert face[1] != 0.0
    assert parry is False
    weapon.trigger(me, view, face)
    assert view.last_velocity is not None
    assert view.last_velocity.y != 0.0


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
    accel, _, _, parry = policy.decide(me, view, 600.0)
    assert accel[1] < 0  # dodges downward
    assert parry is False


def test_dodge_considers_multiple_projectiles() -> None:
    me = EntityId(1)
    enemy = EntityId(2)

    @dataclass
    class ViewWithProjectiles(DummyView):
        projs: list[ProjectileInfo] = field(default_factory=list)

        def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:  # noqa: D401
            return self.projs

    projectiles = [
        ProjectileInfo(owner=enemy, position=(40.0, 0.0), velocity=(-100.0, 0.0)),
        ProjectileInfo(owner=enemy, position=(0.0, 40.0), velocity=(0.0, -100.0)),
    ]
    view = ViewWithProjectiles(me, enemy, (0.0, 0.0), (100.0, 0.0), projs=projectiles)
    policy = SimplePolicy("aggressive", dodge_smoothing=1.0)
    accel, _, _, parry = policy.decide(me, view, 600.0)
    assert accel[0] > 0  # influenced by the top projectile
    assert accel[1] < 0  # still avoids the right projectile
    assert parry is False


def test_dodge_vector_is_smoothed() -> None:
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
    policy = SimplePolicy("aggressive", dodge_smoothing=0.5)
    first, _, _, _ = policy.decide(me, view, 600.0)

    view.proj_pos = (-40.0, 0.0)
    view.proj_vel = (100.0, 0.0)
    second, _, _, _ = policy.decide(me, view, 600.0)

    assert first[1] < 0  # initial dodge downward
    assert second[1] > -0.1  # smoothing prevents immediate flip upward


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
    accel, _, _, parry = policy.decide(me, view, 600.0)
    assert accel[1] < 0  # dodges downward
    assert parry is False


def test_contact_vs_distant_policy_is_aggressive() -> None:
    policy = policy_for_weapon("katana", "shuriken")
    assert policy.style == "aggressive"


def test_contact_vs_contact_policy_is_aggressive() -> None:
    policy = policy_for_weapon("katana", "knife")
    assert policy.style == "aggressive"


def test_distant_vs_contact_policy_is_evader() -> None:
    policy = policy_for_weapon("shuriken", "knife")
    assert policy.style == "evader"


def test_distant_vs_distant_policy_is_kiter() -> None:
    policy = policy_for_weapon("bazooka", "shuriken")
    assert policy.style == "kiter"


def test_distant_policy_no_fire_without_projectile() -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (1000.0, 0.0))
    policy = policy_for_weapon("shuriken", "katana")
    _, _, fire, parry = policy.decide(EntityId(1), view, 600.0)
    assert fire is False
    assert parry is False


def test_distant_policy_targets_projectile_when_enemy_far() -> None:
    me = EntityId(1)
    enemy = EntityId(2)

    @dataclass
    class ViewWithProjectile(DummyView):
        proj: ProjectileInfo = field(
            default_factory=lambda: ProjectileInfo(EntityId(0), (0.0, 0.0), (0.0, 0.0))
        )

        def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:  # noqa: D401
            return [self.proj]

    projectile = ProjectileInfo(owner=enemy, position=(100.0, 100.0), velocity=(0.0, 0.0))
    view = ViewWithProjectile(me, enemy, (0.0, 0.0), (500.0, 0.0), proj=projectile)
    policy = policy_for_weapon("shuriken", "katana")
    _, face, fire, _ = policy.decide(me, view, 600.0)
    assert fire is True
    assert face[0] > 0 and face[1] > 0


def test_evader_moves_toward_offscreen_enemy() -> None:
    view = DummyView(EntityId(1), EntityId(2), (0.0, 0.0), (2000.0, 0.0))
    policy = SimplePolicy("evader", range_type="distant")
    accel, _, _, _ = policy.decide(EntityId(1), view, 600.0)
    assert accel[0] > 0
