from __future__ import annotations

import math
from dataclasses import dataclass

from app.core.types import Damage, EntityId, Vec2

from . import weapon_registry
from .base import Weapon, WorldView


@dataclass(slots=True)
class _Satellite:
    """Rectangular element orbiting around the weapon owner."""

    width: float
    height: float
    radius: float
    angle: float


class OrbitalWeapon(Weapon):
    """Weapon managing satellites rotating around its owner."""

    satellites: list[_Satellite]

    def __init__(
        self, name: str, damage: Damage, speed: float, satellites: list[_Satellite]
    ) -> None:
        super().__init__(name=name, cooldown=0.0, damage=damage, speed=speed)
        self.satellites = satellites

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:
        return None

    def update(self, owner: EntityId, view: WorldView, dt: float) -> None:
        enemy = view.get_enemy(owner)
        if enemy is None:
            return
        enemy_pos = view.get_position(enemy)
        owner_pos = view.get_position(owner)
        for sat in self.satellites:
            sat.angle = (sat.angle + self.speed * dt) % math.tau
            cx = owner_pos[0] + math.cos(sat.angle) * sat.radius
            cy = owner_pos[1] + math.sin(sat.angle) * sat.radius
            if abs(enemy_pos[0] - cx) <= sat.width / 2 and abs(enemy_pos[1] - cy) <= sat.height / 2:
                view.deal_damage(enemy, self.damage)


class KatanaOrbital(OrbitalWeapon):
    """Single thin blade orbiting around the owner."""

    def __init__(self) -> None:
        satellites = [_Satellite(width=80.0, height=12.0, radius=60.0, angle=0.0)]
        super().__init__(name="katana_orbital", damage=Damage(18), speed=4.0, satellites=satellites)


class ShurikenOrbital(OrbitalWeapon):
    """Three small squares orbiting around the owner."""

    def __init__(self) -> None:
        satellites = [
            _Satellite(width=16.0, height=16.0, radius=50.0, angle=0.0),
            _Satellite(width=16.0, height=16.0, radius=50.0, angle=math.tau / 3),
            _Satellite(width=16.0, height=16.0, radius=50.0, angle=2 * math.tau / 3),
        ]
        super().__init__(
            name="shuriken_orbital", damage=Damage(10), speed=4.0, satellites=satellites
        )


weapon_registry.register("katana_orbital", KatanaOrbital)
weapon_registry.register("shuriken_orbital", ShurikenOrbital)
