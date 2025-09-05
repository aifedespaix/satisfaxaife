from __future__ import annotations

import pygame

from app.core.types import Damage
from app.weapons.effects import OrbitingSprite
from tests.helpers import make_controller, make_player


def test_orbiting_sprite_hits_enemy() -> None:
    pygame.init()
    player_a = make_player(1, 0.0, team=0)
    player_b = make_player(2, 60.0, team=1)
    controller = make_controller(player_a, player_b)
    sprite = pygame.Surface((10, 10))
    blade = OrbitingSprite(
        owner=player_a.eid,
        damage=Damage(10.0),
        sprite=sprite,
        radius=20.0,
        angle=0.0,
        speed=0.0,
    )
    controller.effects.append(blade)
    controller._step_effects()
    controller._resolve_effect_hits(0.0)
    assert player_b.ball.health == 90.0
