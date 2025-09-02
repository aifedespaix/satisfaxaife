from __future__ import annotations

from app.core.types import Damage, EntityId, Vec2

from . import weapon_registry
from .assets import load_gravity_well_sprite
from .base import RangeType, Weapon, WorldView
from .effects import GravityWellEffect


class GravityWell(Weapon):
    """Cannon that spawns a temporary gravity field."""

    range_type: RangeType = "distant"

    def __init__(self) -> None:
        super().__init__(
            name="gravity_well",
            cooldown=3.0,
            damage=Damage(10),
            speed=0.0,
            range_type=self.range_type,
        )
        self._sprite = load_gravity_well_sprite()

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:
        origin = view.get_position(owner)
        target = (
            origin[0] + direction[0] * 120.0,
            origin[1] + direction[1] * 120.0,
        )
        effect = GravityWellEffect(
            owner=owner,
            position=target,
            radius=80.0,
            pull_strength=200.0,
            damage_per_second=self.damage.amount,
            ttl=3.0,
        )
        view.spawn_effect(effect)


weapon_registry.register("gravity_well", GravityWell)
