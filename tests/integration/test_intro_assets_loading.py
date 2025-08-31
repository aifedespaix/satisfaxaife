from __future__ import annotations

from pathlib import Path

import pygame

from app.game.match import create_controller
from app.intro import IntroAssets
from tests.integration.helpers import SpyRecorder


def test_intro_assets_load_weapon_images() -> None:
    controller = create_controller("katana", "shuriken", SpyRecorder(), max_seconds=0)
    config = controller.intro_manager.config

    assets = IntroAssets.load(config)

    expected_a = pygame.image.load(str(Path("assets/weapons/katana/weapon.png"))).convert_alpha()
    expected_b = pygame.image.load(str(Path("assets/weapons/shuriken/weapon.png"))).convert_alpha()

    assert pygame.image.tostring(assets.weapon_a, "RGBA") == pygame.image.tostring(
        expected_a, "RGBA"
    )
    assert pygame.image.tostring(assets.weapon_b, "RGBA") == pygame.image.tostring(
        expected_b, "RGBA"
    )
    pygame.quit()
