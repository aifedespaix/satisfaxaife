from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.core.types import EntityId, Vec2
from app.world.projectiles import Projectile

from .base import WeaponEffect, WorldView

if TYPE_CHECKING:
    from app.render.renderer import Renderer


@dataclass(slots=True)
class ParryEffect(WeaponEffect):
    """Short-lived shield that deflects projectiles near its owner."""

    owner: EntityId
    radius: float
    duration: float
    _remaining: float = 0.0

    def __post_init__(self) -> None:
        self._remaining = self.duration

    def step(self, dt: float) -> bool:
        """Decrease remaining parry time and report activity."""
        self._remaining -= dt
        return self._remaining > 0.0

    def collides(self, view: WorldView, position: Vec2, radius: float) -> bool:
        cx, cy = view.get_position(self.owner)
        dx = cx - position[0]
        dy = cy - position[1]
        return dx * dx + dy * dy <= (self.radius + radius) ** 2

    def on_hit(self, view: WorldView, target: EntityId, timestamp: float) -> bool:  # noqa: D401
        return True

    def deflect_projectile(self, view: WorldView, projectile: Projectile, timestamp: float) -> None:
        """Reflect ``projectile`` away from the owner."""
        enemy = view.get_enemy(self.owner)
        if enemy is not None:
            target = view.get_position(enemy)
            projectile.retarget(target, self.owner)
        else:
            vx, vy = projectile.body.velocity
            projectile.body.velocity = (-vx, -vy)
            projectile.owner = self.owner
            projectile.ttl = projectile.max_ttl
        if projectile.audio is not None:
            projectile.audio.on_touch(timestamp)

    def draw(self, renderer: Renderer, view: WorldView) -> None:  # noqa: D401
        if renderer.debug:
            center = view.get_position(self.owner)
            renderer.draw_circle_outline(center, self.radius, (0, 255, 0))

    def destroy(self) -> None:  # noqa: D401
        return None
