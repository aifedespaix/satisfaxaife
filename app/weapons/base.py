"""Core weapon interfaces and types.

Contact weapons are responsible for deflecting projectiles via their own
hitboxes. No separate parry effect is used.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol

from app.core.types import Color, Damage, EntityId, ProjectileInfo, Vec2

if TYPE_CHECKING:
    import pygame

    from app.render.renderer import Renderer


class WorldView(Protocol):
    """Minimal interface exposed to weapons."""

    def get_enemy(self, owner: EntityId) -> EntityId | None:
        """Return the enemy entity id for *owner*."""

    def get_position(self, eid: EntityId) -> Vec2:
        """Return the current position of an entity."""

    def get_velocity(self, eid: EntityId) -> Vec2:
        """Return the current velocity vector of an entity."""

    def get_health_ratio(self, eid: EntityId) -> float:
        """Return the current health ratio ``health / max_health`` of an entity."""

    def get_team_color(self, eid: EntityId) -> Color:
        """Return the color of the team owning ``eid``."""

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:
        """Apply ``damage`` to ``eid`` at the given ``timestamp``."""

    def heal(self, eid: EntityId, amount: float, timestamp: float) -> None:
        """Restore ``amount`` health to ``eid`` at the given ``timestamp``."""

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:
        """Apply an impulse to the entity's body.

        Raises
        ------
        KeyError
            If ``eid`` does not reference a known entity.
        """

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:
        """Increase ``eid``'s maximum speed by ``bonus`` units."""

    def spawn_effect(self, effect: WeaponEffect) -> None:
        """Register a new weapon effect to be processed by the match."""

    def spawn_projectile(
        self,
        owner: EntityId,
        position: Vec2,
        velocity: Vec2,
        radius: float,
        damage: Damage,
        knockback: float,
        ttl: float,
        sprite: pygame.Surface | None = None,
        spin: float = 0.0,
        trail_color: Color | None = None,
        acceleration: float = 0.0,
    ) -> WeaponEffect:
        """Spawn a projectile owned by *owner* and register it."""

    def iter_projectiles(self, excluding: EntityId | None = None) -> Iterable[ProjectileInfo]:
        """Yield active projectiles, optionally skipping those owned by *excluding*."""

    def get_weapon(self, eid: EntityId) -> Weapon:
        """Return the weapon currently wielded by ``eid``."""


class WeaponEffect(Protocol):
    """Dynamic entity created by a weapon."""

    owner: EntityId

    def step(self, dt: float) -> bool:
        """Advance state and return ``True`` while the effect is active."""

    def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:
        """Return ``True`` if the effect intersects a circle at *position*."""

    def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool:
        """Handle a collision with ``target`` at ``timestamp`` and return ``True`` to keep the effect."""

    def draw(self, renderer: Renderer, view: WorldView) -> None:
        """Render the effect on *renderer*."""

    def destroy(self) -> None:
        """Clean up resources when the effect is removed."""


RangeType = Literal["contact", "distant"]


@dataclass(slots=True)
class Weapon:
    """Base weapon with a cooldown timer.

    Attributes
    ----------
    name:
        Unique weapon identifier.
    cooldown:
        Minimum delay in seconds between two consecutive shots.
    damage:
        Amount of damage inflicted on each successful hit.
    speed:
        Velocity of the weapon's projectile or effect in units per second.
    _timer:
        Internal cooldown tracker used to throttle fire rate.
    """

    name: str
    cooldown: float
    damage: Damage
    speed: float = 0.0
    range_type: RangeType = "contact"
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
