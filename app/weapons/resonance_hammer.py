from __future__ import annotations

# ruff: noqa: E402

"""Resonance Hammer weapon emitting a reflective shockwave.

Assets for this weapon are not yet available; placeholder visuals are used
until dedicated sprites and audio are integrated."""

from app.core.types import Damage, EntityId, Vec2

from . import weapon_registry
from .assets import load_resonance_hammer_sprite
from .base import RangeType, Weapon, WorldView
from .effects import ResonanceWaveEffect


class ResonanceHammer(Weapon):
    """Heavy hammer emitting a resonant shockwave on impact."""

    range_type: RangeType = "contact"

    def __init__(self) -> None:
        super().__init__(
            name="resonance_hammer",
            cooldown=2.0,
            damage=Damage(12),
            speed=120.0,
            range_type=self.range_type,
        )
        self._sprite = load_resonance_hammer_sprite()

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:
        origin = view.get_position(owner)
        effect = ResonanceWaveEffect(
            owner=owner,
            position=origin,
            max_radius=120.0,
            speed=self.speed,
            damage=self.damage,
            amplification=2.0,
        )
        view.spawn_effect(effect)


weapon_registry.register("resonance_hammer", ResonanceHammer)
