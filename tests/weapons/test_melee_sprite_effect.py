from __future__ import annotations

import sys
import types
from dataclasses import dataclass, field
from typing import cast

import pygame

from app.core.types import Damage, EntityId, ProjectileInfo, Vec2


class _Surface:
    def get_width(self) -> int:  # pragma: no cover - simple stub
        return 10

    def get_height(self) -> int:  # pragma: no cover - simple stub
        return 10

    def get_size(self) -> tuple[int, int]:  # pragma: no cover - simple stub
        return (self.get_width(), self.get_height())


pygame.Surface = _Surface
pygame.transform = types.SimpleNamespace(rotate=lambda surf, angle: surf)
pygame.mixer = types.SimpleNamespace(init=lambda **kwargs: None)


assets_mod = types.ModuleType("app.weapons.assets")


def _load_weapon_sprite(name: str, max_dim: float | None = None) -> pygame.Surface:
    return _Surface()


assets_mod.load_weapon_sprite = _load_weapon_sprite  # type: ignore[attr-defined]
sys.modules.setdefault("app.weapons.assets", assets_mod)


audio_mod = types.ModuleType("app.audio.weapons")


class _WeaponAudio:
    def __init__(self, *args: object, **kwargs: object) -> None:  # noqa: D401
        return None

    def start_idle(self) -> None:  # noqa: D401
        return None

    def on_touch(self, timestamp: float) -> None:  # noqa: D401
        return None


audio_mod.WeaponAudio = _WeaponAudio  # type: ignore[attr-defined]
sys.modules.setdefault("app.audio.weapons", audio_mod)

from app.weapons.base import Weapon, WeaponEffect, WorldView  # noqa: E402
from app.weapons.katana import Katana  # noqa: E402
from app.weapons.knife import Knife  # noqa: E402


@dataclass(slots=True)
class DummyView(WorldView):
    positions: dict[EntityId, Vec2]
    effects: list[WeaponEffect] = field(default_factory=list)
    speed_bonus: dict[EntityId, float] = field(default_factory=dict)

    def get_position(self, eid: EntityId) -> Vec2:  # noqa: D401
        return self.positions[eid]

    def get_velocity(self, eid: EntityId) -> Vec2:  # pragma: no cover - unused
        return (0.0, 0.0)

    def get_health_ratio(self, eid: EntityId) -> float:  # pragma: no cover - unused
        return 1.0

    def get_team_color(self, eid: EntityId) -> tuple[int, int, int]:  # pragma: no cover - simple
        return (int(eid), 0, 0)

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:  # noqa: D401
        return None

    def heal(self, eid: EntityId, amount: float, timestamp: float) -> None:  # noqa: D401
        return None

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:  # noqa: D401
        return None

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:  # noqa: D401
        self.speed_bonus[eid] = self.speed_bonus.get(eid, 0.0) + bonus

    def spawn_effect(self, effect: WeaponEffect) -> None:  # noqa: D401
        self.effects.append(effect)

    def spawn_projectile(
        self, *args: object, **kwargs: object
    ) -> WeaponEffect:  # pragma: no cover - unused
        raise NotImplementedError

    def iter_projectiles(
        self, excluding: EntityId | None = None
    ) -> list[ProjectileInfo]:  # pragma: no cover - unused
        return []

    def get_weapon(self, eid: EntityId) -> Weapon:  # pragma: no cover - unused
        raise NotImplementedError

    def get_enemy(self, owner: EntityId) -> EntityId | None:  # pragma: no cover - unused
        return None


def _assert_weapon_spawns_sprite(weapon: Knife | Katana) -> None:
    owner = EntityId(1)
    view = DummyView({owner: (0.0, 0.0)})
    weapon.update(owner, cast(WorldView, view), dt=0.016)
    assert view.effects, "Weapon did not spawn any effect"
    effect = view.effects[0]
    sprite = getattr(effect, "sprite", None)
    assert isinstance(sprite, pygame.Surface)


def test_knife_spawns_sprite_effect() -> None:
    _assert_weapon_spawns_sprite(Knife())


def test_katana_spawns_sprite_effect() -> None:
    _assert_weapon_spawns_sprite(Katana())
