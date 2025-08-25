from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.types import Damage, EntityId, Vec2


class WorldView(Protocol):
    """Minimal interface exposed to weapons."""

    def get_enemy(self, owner: EntityId) -> EntityId | None:
        """Return the enemy entity id for *owner*."""

    def get_position(self, eid: EntityId) -> Vec2:
        """Return the current position of an entity."""

    def get_health_ratio(self, eid: EntityId) -> float:
        """Return the current health ratio ``health / max_health`` of an entity."""

    def deal_damage(self, eid: EntityId, damage: Damage) -> None:
        """Apply *damage* to the entity."""

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:
        """Apply an impulse to the entity's body."""

    def spawn_projectile(
        self,
        owner: EntityId,
        position: Vec2,
        velocity: Vec2,
        radius: float,
        damage: Damage,
        knockback: float,
        ttl: float,
    ) -> None:
        """Spawn a projectile owned by *owner*."""


@dataclass(slots=True)
class Weapon:
    """Base weapon with a cooldown timer."""

    name: str
    cooldown: float
    damage: Damage
    _timer: float = 0.0

    def step(self, dt: float) -> None:
        """Advance internal cooldown timer."""
        if self._timer > 0:
            self._timer = max(0.0, self._timer - dt)

    def update(self, owner: EntityId, view: WorldView, dt: float) -> None:
        """Update weapon state every frame.

        Parameters
        ----------
        owner : EntityId
            Entity identifier owning the weapon.
        view : WorldView
            Read-only access to the game state.
        dt : float
            Time delta for the current frame in seconds.

        Notes
        -----
        Subclasses may override to implement continuous effects such as
        beams or shields. The default implementation does nothing, making
        the method optional for weapons that only react when fired.
        """

        return None

    def trigger(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:
        """Attempt to fire the weapon from *owner* facing *direction*."""
        if self._timer > 0:
            return
        self._fire(owner, view, direction)
        self._timer = self.cooldown

    def _fire(self, owner: EntityId, view: WorldView, direction: Vec2) -> None:
        """Execute the weapon's effect. Subclasses must override."""
        raise NotImplementedError
