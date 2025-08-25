from __future__ import annotations

import math
from dataclasses import dataclass

import pygame

from app.core.types import Damage, EntityId, Vec2
from app.render.renderer import Renderer

from . import weapon_registry
from .base import Weapon, WeaponEffect, WorldView


@dataclass(slots=True)
class _SatelliteSpec:
    """Static parameters describing a satellite."""

    width: float
    height: float
    radius: float
    angle: float


@dataclass(slots=True)
class SatelliteEffect(WeaponEffect):
    """Rectangular element orbiting around the weapon owner."""

    owner: EntityId
    damage: Damage
    width: float
    height: float
    radius: float
    angle: float
    speed: float

    def step(self, dt: float) -> bool:
        self.angle = (self.angle + self.speed * dt) % math.tau
        return True

    def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:
        owner_pos = view.get_position(self.owner)
        cx = owner_pos[0] + math.cos(self.angle) * self.radius
        cy = owner_pos[1] + math.sin(self.angle) * self.radius
        return abs(position[0] - cx) <= self.width / 2 and abs(position[1] - cy) <= self.height / 2

    def on_hit(self, view: WorldView, target: EntityId) -> bool:
        view.deal_damage(target, self.damage)
        return True

    def draw(self, renderer: Renderer, view: WorldView) -> None:
        owner_pos = view.get_position(self.owner)
        cx = owner_pos[0] + math.cos(self.angle) * self.radius
        cy = owner_pos[1] + math.sin(self.angle) * self.radius
        rect = pygame.Rect(0, 0, int(self.width), int(self.height))
        rect.center = (int(cx), int(cy))
        pygame.draw.rect(renderer.surface, (255, 255, 255), rect)

    def destroy(self) -> None:
        return None


class OrbitalWeapon(Weapon):
    """Weapon managing satellites rotating around its owner."""

    _specs: list[_SatelliteSpec]
    _initialized: bool

    def __init__(
        self, name: str, damage: Damage, speed: float, satellites: list[_SatelliteSpec]
    ) -> None:
        super().__init__(name=name, cooldown=0.0, damage=damage, speed=speed)
        self._specs = satellites
        self._initialized = False

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:
        return None

    def update(self, owner: EntityId, view: WorldView, dt: float) -> None:
        if not self._initialized:
            for spec in self._specs:
                view.spawn_effect(
                    SatelliteEffect(
                        owner=owner,
                        damage=self.damage,
                        width=spec.width,
                        height=spec.height,
                        radius=spec.radius,
                        angle=spec.angle,
                        speed=self.speed,
                    )
                )
            self._initialized = True


class KatanaOrbital(OrbitalWeapon):
    """Single thin blade orbiting around the owner."""

    def __init__(self) -> None:
        satellites = [_SatelliteSpec(width=80.0, height=12.0, radius=60.0, angle=0.0)]
        super().__init__(name="katana_orbital", damage=Damage(18), speed=4.0, satellites=satellites)


class ShurikenOrbital(OrbitalWeapon):
    """Three small squares orbiting around the owner."""

    def __init__(self) -> None:
        satellites = [
            _SatelliteSpec(width=16.0, height=16.0, radius=50.0, angle=0.0),
            _SatelliteSpec(width=16.0, height=16.0, radius=50.0, angle=math.tau / 3),
            _SatelliteSpec(width=16.0, height=16.0, radius=50.0, angle=2 * math.tau / 3),
        ]
        super().__init__(
            name="shuriken_orbital", damage=Damage(10), speed=4.0, satellites=satellites
        )


weapon_registry.register("katana_orbital", KatanaOrbital)
weapon_registry.register("shuriken_orbital", ShurikenOrbital)
