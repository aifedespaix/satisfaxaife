from __future__ import annotations

import sys
from typing import cast

# Ensure real weapon modules are used rather than the test stubs installed in
# ``tests/conftest.py``.
sys.modules.pop("app.weapons", None)
sys.modules.pop("app.weapons.base", None)
sys.modules.pop("app.weapons.shuriken", None)
sys.modules.pop("pygame", None)
sys.modules.pop("pygame.sndarray", None)
import pygame as _pygame  # noqa: F401, E402  - ensure real pygame is loaded

from app.audio.weapons import WeaponAudio  # noqa: E402
from app.core.types import Damage, EntityId, Vec2  # noqa: E402
from app.weapons.base import WeaponEffect, WorldView  # noqa: E402
from app.weapons.bazooka import Bazooka  # noqa: E402
from app.weapons.katana import Katana  # noqa: E402
from app.weapons.knife import Knife  # noqa: E402
from app.weapons.shuriken import Shuriken  # noqa: E402
from app.world.physics import PhysicsWorld  # noqa: E402
from app.world.projectiles import Projectile  # noqa: E402


class StubAudio:
    def __init__(self) -> None:
        self.idle_started = False
        self.thrown = False
        self.touched = False
        self.on_throw_calls = 0

    def start_idle(self, timestamp: float | None = None) -> None:  # noqa: D401
        self.idle_started = True

    def on_throw(self, timestamp: float | None = None) -> None:  # noqa: D401
        self.thrown = True
        self.on_throw_calls += 1

    def on_touch(self, timestamp: float | None = None) -> None:  # noqa: D401
        self.touched = True


class ProjectileView:
    """Test view that records spawned projectiles."""

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
        trail_color: tuple[int, int, int] | None = None,
        acceleration: float = 0.0,
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
            trail_color,
            acceleration,
        )
        self.projectile = proj
        return proj

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:  # noqa: D401
        pass

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
        pass


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

        def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
            pass

    view_obj = View()
    view = cast(WorldView, view_obj)
    katana.update(EntityId(1), view, 0.0)
    assert stub_audio.idle_started
    effect = view_obj.effects[0]
    effect.on_hit(view, EntityId(2), timestamp=0.0)
    assert stub_audio.touched


def test_knife_audio_events() -> None:
    knife = Knife()
    stub_audio = StubAudio()
    knife.audio = cast(WeaponAudio, stub_audio)

    class View:
        def __init__(self) -> None:
            self.effects: list[WeaponEffect] = []

        def spawn_effect(self, effect: WeaponEffect) -> None:  # noqa: D401
            self.effects.append(effect)

        def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
            return (0.0, 0.0)

        def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:  # noqa: D401
            pass

        def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # noqa: D401
            pass

        def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
            pass

    view_obj = View()
    view = cast(WorldView, view_obj)
    knife.update(EntityId(1), view, 0.0)
    assert stub_audio.idle_started
    effect = view_obj.effects[0]
    effect.on_hit(view, EntityId(2), timestamp=0.0)
    assert stub_audio.touched


def test_shuriken_audio_events() -> None:
    shuriken = Shuriken()
    stub_audio = StubAudio()
    shuriken.audio = cast(WeaponAudio, stub_audio)

    view_obj = ProjectileView()
    view = cast(WorldView, view_obj)
    shuriken._fire(EntityId(1), view, (1.0, 0.0))
    assert stub_audio.on_throw_calls == 1
    projectile = view_obj.projectile
    assert projectile is not None
    projectile.on_hit(view, EntityId(2), timestamp=0.0)
    assert stub_audio.touched


def test_bazooka_audio_events() -> None:
    bazooka = Bazooka()
    stub_audio = StubAudio()
    bazooka.audio = cast(WeaponAudio, stub_audio)

    view_obj = ProjectileView()
    view = cast(WorldView, view_obj)
    bazooka._fire(EntityId(1), view, (1.0, 0.0))
    assert stub_audio.on_throw_calls == 1
    projectile = view_obj.projectile
    assert projectile is not None
    projectile.on_hit(view, EntityId(2), timestamp=0.0)
    assert stub_audio.touched


def test_shuriken_multiple_fires_call_on_throw_each_time() -> None:
    shuriken = Shuriken()
    stub_audio = StubAudio()
    shuriken.audio = cast(WeaponAudio, stub_audio)

    view_obj = ProjectileView()
    view = cast(WorldView, view_obj)
    shots = 3
    for count in range(1, shots + 1):
        shuriken._fire(EntityId(1), view, (1.0, 0.0))
        assert stub_audio.on_throw_calls == count


def test_bazooka_multiple_fires_call_on_throw_each_time() -> None:
    bazooka = Bazooka()
    stub_audio = StubAudio()
    bazooka.audio = cast(WeaponAudio, stub_audio)

    view_obj = ProjectileView()
    view = cast(WorldView, view_obj)
    shots = 5
    for count in range(1, shots + 1):
        bazooka._fire(EntityId(1), view, (1.0, 0.0))
        assert stub_audio.on_throw_calls == count
