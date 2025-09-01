from __future__ import annotations

import os
import sys
from pathlib import Path
import types
from typing import Protocol

from app.core.types import Damage, EntityId, Vec2

# Ensure pygame uses dummy drivers during tests so that audio and video
# initialization works in headless environments.
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Provide a minimal pygame stub so that modules depending on pygame can be
# imported without requiring the full library during tests.
_pygame_stub = types.ModuleType("pygame")
_pygame_stub.Surface = object  # type: ignore[attr-defined]
_pygame_stub.sndarray = types.ModuleType("pygame.sndarray")  # type: ignore[attr-defined]
_pygame_stub.sndarray.array = lambda *a, **k: None
sys.modules.setdefault("pygame", _pygame_stub)
sys.modules.setdefault("pygame.sndarray", _pygame_stub.sndarray)

_renderer_stub = types.ModuleType("app.render.renderer")
_renderer_stub.Renderer = object  # type: ignore[attr-defined]
sys.modules.setdefault("app.render.renderer", _renderer_stub)

sys.modules.setdefault("numpy", types.ModuleType("numpy"))

_weapons_base = types.ModuleType("app.weapons.base")


class WorldView(Protocol):
    def get_enemy(self, owner: EntityId) -> EntityId | None: ...

    def get_position(self, eid: EntityId) -> Vec2: ...

    def get_velocity(self, eid: EntityId) -> Vec2: ...

    def get_health_ratio(self, eid: EntityId) -> float: ...

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None: ...

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None: ...

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None: ...

    def spawn_effect(self, effect: "WeaponEffect") -> None: ...

    def spawn_projectile(self, *args: object, **kwargs: object) -> "WeaponEffect": ...

    def iter_projectiles(self, excluding: EntityId | None = None) -> object: ...


class WeaponEffect(Protocol):
    owner: EntityId

    def step(self, dt: float) -> bool: ...

    def collides(self, view: WorldView, position: Vec2, radius: float) -> bool: ...

    def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool: ...

    def draw(self, renderer: object, view: WorldView) -> None: ...

    def destroy(self) -> None: ...


_weapons_base.WorldView = WorldView  # type: ignore[attr-defined]
_weapons_base.WeaponEffect = WeaponEffect  # type: ignore[attr-defined]
sys.modules.setdefault("app.weapons", types.ModuleType("app.weapons"))
sys.modules["app.weapons.base"] = _weapons_base
_shuriken_stub = types.ModuleType("app.weapons.shuriken")
_shuriken_stub.Shuriken = object  # type: ignore[attr-defined]
sys.modules.setdefault("app.weapons.shuriken", _shuriken_stub)
