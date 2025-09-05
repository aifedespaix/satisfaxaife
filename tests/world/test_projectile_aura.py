from __future__ import annotations

from typing import cast

from app.core.types import Damage, EntityId
from app.render.renderer import Renderer
from app.weapons.base import WorldView
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


class DummyRenderer:
    def __init__(self) -> None:  # pragma: no cover - simple init
        self.calls: list[tuple[tuple[float, float], int, tuple[int, int, int]]] = []
        self.debug = False

    def draw_sprite(
        self,
        sprite: object,
        pos: tuple[float, float],
        angle: float,
        aura_color: tuple[int, int, int] | None = None,
        aura_radius: int | None = None,
    ) -> None:
        if aura_color is not None and aura_radius is not None:
            self.calls.append((pos, aura_radius + 2, aura_color))


class DummyView:
    def get_team_color(self, owner: EntityId) -> tuple[int, int, int]:
        return (1, 2, 3)

    def heal(self, eid: EntityId, amount: float, timestamp: float) -> None:  # pragma: no cover - unused
        return None


def test_projectile_sprite_has_aura() -> None:
    world = PhysicsWorld()
    projectile = Projectile.spawn(
        world,
        owner=EntityId(1),
        position=(0.0, 0.0),
        velocity=(0.0, 0.0),
        radius=5.0,
        damage=Damage(1),
        knockback=0.0,
        ttl=1.0,
        sprite=object(),
    )
    renderer = DummyRenderer()
    view = DummyView()
    projectile.draw(cast(Renderer, renderer), cast(WorldView, view))
    assert renderer.calls == [((0.0, 0.0), 5, (1, 2, 3))]
