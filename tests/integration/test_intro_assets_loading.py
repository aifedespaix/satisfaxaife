from __future__ import annotations

from collections import defaultdict

import pygame

from app.core.config import settings
from app.game.match import create_controller
from tests.integration.helpers import SpyRecorder


def test_intro_assets_loaded_and_drawn_once() -> None:
    load_counts: dict[str, int] = defaultdict(int)
    original_load = pygame.image.load

    def counting_load(path: str) -> pygame.Surface:
        for key in ("vs.png", "katana/weapon.png", "shuriken/weapon.png"):
            if path.endswith(key):
                load_counts[key] += 1
        return original_load(path)

    pygame.image.load = counting_load
    controller = create_controller("katana", "shuriken", SpyRecorder(), max_seconds=0)
    intro = controller.intro_manager

    try:
        assert load_counts["vs.png"] == 1
        assert load_counts["katana/weapon.png"] == 1
        assert load_counts["shuriken/weapon.png"] == 1

        assets = intro._renderer.assets
        assert assets is not None
        counts = {id(assets.logo): 0, id(assets.weapon_a): 0, id(assets.weapon_b): 0}
        original_rotozoom = pygame.transform.rotozoom

        def counting_rotozoom(
            surface: pygame.Surface, angle: float, scale: float
        ) -> pygame.Surface:
            key = id(surface)
            if key in counts:
                counts[key] += 1
            return original_rotozoom(surface, angle, scale)

        pygame.transform.rotozoom = counting_rotozoom
        surface = pygame.Surface((settings.width, settings.height))

        intro.start()
        while not intro.is_finished():
            for k in counts:
                counts[k] = 0
            intro.draw(surface, ("", ""))
            for v in counts.values():
                assert v == 1
            intro.update(1.0)
    finally:
        pygame.transform.rotozoom = original_rotozoom
        pygame.image.load = original_load
        pygame.quit()
