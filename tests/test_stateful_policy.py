from __future__ import annotations

from dataclasses import dataclass, field

from app.ai.stateful_policy import State, StatefulPolicy, policy_for_weapon
from app.core.types import Damage, EntityId, ProjectileInfo, Vec2
from app.weapons.base import WeaponEffect, WorldView


@dataclass
class DummyView(WorldView):
    me: EntityId
    enemy: EntityId
    pos_me: Vec2
    pos_enemy: Vec2
    vel_enemy: Vec2 = (0.0, 0.0)
    health_me: float = 1.0
    health_enemy: float = 1.0
    projectiles: list[ProjectileInfo] = field(default_factory=list)

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.enemy

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.pos_me if eid == self.me else self.pos_enemy

    def get_velocity(self, eid: EntityId) -> Vec2:  # noqa: D401
        return (0.0, 0.0) if eid == self.me else self.vel_enemy

    def get_health_ratio(self, eid: EntityId) -> float:  # noqa: D401
        return self.health_me if eid == self.me else self.health_enemy

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:  # noqa: D401
        return None

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
        return None

    def spawn_effect(self, effect: WeaponEffect) -> None:  # noqa: D401
        return None

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # noqa: D401
        return None

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
        raise NotImplementedError

    def iter_projectiles(self, excluding: EntityId | None = None) -> list[ProjectileInfo]:  # noqa: D401
        return self.projectiles


def test_attack_then_dodge() -> None:
    me = EntityId(1)
    enemy = EntityId(2)
    view = DummyView(me, enemy, (0.0, 0.0), (100.0, 0.0))
    policy = StatefulPolicy("aggressive", transition_time=0.0)
    policy.decide(me, view, 0.0, 600.0)
    assert policy.state is State.ATTACK

    projectile = ProjectileInfo(owner=enemy, position=(50.0, 0.0), velocity=(-80.0, 0.0))
    view.projectiles = [projectile]
    policy.decide(me, view, 0.0, 600.0)
    assert policy.state == State.DODGE  # type: ignore[comparison-overlap]


def test_parry_reduces_damage() -> None:
    me = EntityId(1)
    enemy = EntityId(2)
    projectile = ProjectileInfo(owner=enemy, position=(20.0, 0.0), velocity=(-200.0, 0.0))
    view = DummyView(me, enemy, (0.0, 0.0), (100.0, 0.0), projectiles=[projectile])
    policy = StatefulPolicy("aggressive", transition_time=0.0)
    policy.decide(me, view, 0.0, 600.0)
    assert policy.state is State.PARRY
    reduced = policy.parry_damage(Damage(10.0))
    assert reduced.amount == 0.0


def test_retreat_on_low_health() -> None:
    me = EntityId(1)
    enemy = EntityId(2)
    view = DummyView(me, enemy, (0.0, 0.0), (100.0, 0.0), health_me=0.1)
    policy = StatefulPolicy("aggressive", transition_time=0.0)
    accel, _, _, _ = policy.decide(me, view, 0.0, 600.0)
    assert policy.state is State.RETREAT
    assert accel[0] < 0


def test_mode_transition() -> None:
    me = EntityId(1)
    enemy = EntityId(2)
    view = DummyView(me, enemy, (0.0, 0.0), (100.0, 0.0))
    policy = StatefulPolicy("aggressive", transition_time=1.0)
    accel, _, _, _ = policy.decide(me, view, 0.5, 600.0)
    assert accel[0] < 0  # defensive: keep distance
    accel, _, _, _ = policy.decide(me, view, 1.5, 600.0)
    assert accel[0] > 0  # offensive: close in


def test_melee_dash_modes() -> None:
    me = EntityId(1)
    enemy = EntityId(2)
    view = DummyView(me, enemy, (0.0, 0.0), (100.0, 0.0))
    policy = policy_for_weapon("katana", "bazooka", transition_time=1.0)
    defensive = policy.dash_direction(me, view, 0.5, lambda _: True)
    assert defensive is not None and defensive[0] < 0
    offensive = policy.dash_direction(me, view, 1.5, lambda _: True)
    assert offensive is not None and offensive[0] > 0
