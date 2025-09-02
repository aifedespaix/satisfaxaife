from __future__ import annotations

import math
from dataclasses import dataclass

from app.core.types import Vec2

INVULNERABILITY_BUFFER = 1.0 / 60.0
"""Extra time in seconds after dash end before collisions resume."""


@dataclass(slots=True)
class Dash:
    """Handle dash state and parameters."""

    speed: float = 800.0
    duration: float = 0.2
    cooldown: float = 3.0
    is_dashing: bool = False
    cooldown_end: float = 0.0
    invulnerable_until: float = 0.0
    has_hit: bool = False
    _direction: Vec2 = (0.0, 0.0)
    _dash_end: float = 0.0

    def can_dash(self, now: float) -> bool:
        """Return True if a dash can start at ``now``."""
        return not self.is_dashing and now >= self.cooldown_end

    def start(self, direction: Vec2, now: float) -> None:
        """Start a dash in ``direction`` at ``now`` if possible."""
        if not self.can_dash(now):
            return
        norm = math.hypot(*direction)
        if norm <= 1e-6:
            return
        self.is_dashing = True
        self._direction = (direction[0] / norm, direction[1] / norm)
        self._dash_end = now + self.duration
        self.cooldown_end = now + self.cooldown
        self.invulnerable_until = self._dash_end + INVULNERABILITY_BUFFER
        self.has_hit = False

    def update(self, now: float) -> None:
        """Advance the dash state based on ``now``."""
        if self.is_dashing and now >= self._dash_end:
            self.is_dashing = False

    @property
    def direction(self) -> Vec2:
        """Return the unit direction of the current dash."""
        return self._direction
