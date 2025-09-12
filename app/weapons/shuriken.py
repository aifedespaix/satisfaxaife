from __future__ import annotations

from app.audio.weapons import WeaponAudio
from app.core.types import Damage, EntityId, Vec2
from app.world.entities import DEFAULT_BALL_RADIUS
from app.world.projectiles import Projectile

from . import weapon_registry
from .assets import load_weapon_sprite
from .base import RangeType, Weapon, WorldView


class Shuriken(Weapon):
    """Ranged projectile weapon."""

    range_type: RangeType = "distant"

    def __init__(self) -> None:
        super().__init__(
            name="shuriken",
            cooldown=0.8,
            damage=Damage(8),
            speed=500.0,
            range_type=self.range_type,
        )
        self.audio = WeaponAudio("throw", "shuriken")
        self._radius = DEFAULT_BALL_RADIUS / 3.0
        sprite_size = self._radius * 2.0
        self._sprite = load_weapon_sprite("shuriken", max_dim=sprite_size)

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:
        # Provide deterministic timestamp for audio capture.
        timestamp: float | None
        try:
            timestamp = float(view.get_time())
        except Exception:
            timestamp = None
        self.audio.on_throw(timestamp)
        velocity = (direction[0] * self.speed, direction[1] * self.speed)
        position = view.get_position(owner)
        proj = view.spawn_projectile(
            owner,
            position,
            velocity,
            radius=self._radius,
            damage=self.damage,
            knockback=120.0,
            ttl=0.8,
            sprite=self._sprite,
            spin=12.0,
        )
        if isinstance(proj, Projectile):
            proj.audio = self.audio


weapon_registry.register("shuriken", Shuriken)
