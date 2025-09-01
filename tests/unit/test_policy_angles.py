from __future__ import annotations

from dataclasses import dataclass, field

from app.ai.policy import SimplePolicy
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
    last_velocity: Vec2 | None = field(default=None, init=False)

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # noqa: D401
        return self.enemy

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.pos_me if eid == self.me else self.pos_enemy

    def get_velocity(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.vel_me if eid == self.me else self.vel_enemy

    def get_health_ratio(self, eid: EntityId) -> float:  # noqa: D401
        return 1.0

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


def test_policy_angle_has_vertical_component() -> None:
    me = EntityId(1)
    enemy = EntityId(2)
    view = DummyView(me, enemy, (0.0, 0.0), (50.0, 0.0))
    policy = SimplePolicy("aggressive")
    accel, face, fire = policy.decide(me, view, 600.0)
    assert fire is True
    assert face[1] != 0.0
    weapon = Shuriken()
    weapon.trigger(me, view, face)
    assert view.last_velocity is not None
    assert view.last_velocity[1] != 0.0
