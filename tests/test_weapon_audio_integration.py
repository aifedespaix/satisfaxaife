from __future__ import annotations

from typing import cast

from app.audio.weapons import WeaponAudio
from app.core.types import Damage, EntityId, Vec2
from app.weapons.base import WeaponEffect, WorldView
from app.weapons.katana import Katana
from app.weapons.shuriken import Shuriken
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


class StubAudio:
    def __init__(self) -> None:
        self.idle_started = False
        self.thrown = False
        self.touched = False

    def start_idle(self, timestamp: float | None = None) -> None:  # noqa: D401
        self.idle_started = True

    def on_throw(self, timestamp: float | None = None) -> None:  # noqa: D401
        self.thrown = True

    def on_touch(self, timestamp: float | None = None) -> None:  # noqa: D401
        self.touched = True


def test_katana_audio_events() -> None:
    katana = Katana()
    stub_audio = StubAudio()
    katana.audio = cast(WeaponAudio, stub_audio)

    class View:
        def __init__(self) -> None:
            self.effects: list[WeaponEffect] = []

        def spawn_effect(self, effect: WeaponEffect) -> None:  # noqa: D401
            self.effects.append(effect)

        def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
            return (0.0, 0.0)

        def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:  # noqa: D401
            pass

    view_obj = View()
    view = cast(WorldView, view_obj)
    katana.update(EntityId(1), view, 0.0)
    assert stub_audio.idle_started
    effect = view_obj.effects[0]
    effect.on_hit(view, EntityId(2), timestamp=0.0)
    assert stub_audio.touched


def test_shuriken_audio_events() -> None:
    shuriken = Shuriken()
    stub_audio = StubAudio()
    shuriken.audio = cast(WeaponAudio, stub_audio)

    class View:
        def __init__(self) -> None:
            self.world = PhysicsWorld()
            self.projectile: Projectile | None = None

        def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
            return (0.0, 0.0)

        def spawn_projectile(
            self,
            owner: EntityId,
            position: Vec2,
            velocity: Vec2,
            *,
            radius: float,
            damage: Damage,
            knockback: float,
            ttl: float,
            sprite: object | None = None,
            spin: float = 0.0,
        ) -> WeaponEffect:
            proj = Projectile.spawn(
                self.world,
                owner,
                position,
                velocity,
                radius,
                damage,
                knockback,
                ttl,
                sprite,
                spin,
            )
            self.projectile = proj
            return proj

        def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:  # noqa: D401
            pass

        def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
            pass

    view_obj = View()
    view = cast(WorldView, view_obj)
    shuriken._fire(EntityId(1), view, (1.0, 0.0))
    assert stub_audio.thrown
    projectile = view_obj.projectile
    assert projectile is not None
    projectile.on_hit(view, EntityId(2), timestamp=0.0)
    assert stub_audio.touched
