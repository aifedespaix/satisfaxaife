from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from app.intro import IntroAssets, IntroConfig
from app.intro.assets import FALLBACK_COLOR


def test_assets_load_existing() -> None:
    pygame.init()
    config = IntroConfig(
        font_path=Path("assets/fonts/FightKickDemoRegular.ttf"),
        logo_path=Path("assets/vs.png"),
    )
    assets = IntroAssets.load(config)
    assert isinstance(assets.font, pygame.font.Font)
    assert assets.logo.get_at((0, 0)) != FALLBACK_COLOR
    pygame.quit()


def test_assets_load_fallback(caplog: pytest.LogCaptureFixture) -> None:
    pygame.init()
    caplog.set_level(logging.WARNING)
    config = IntroConfig(
        font_path=Path("missing_font.ttf"),
        logo_path=Path("missing_image.png"),
    )
    assets = IntroAssets.load(config)
    assert "Missing font" in caplog.text
    assert "Missing image" in caplog.text
    assert assets.logo.get_at((0, 0)) == FALLBACK_COLOR
    pygame.quit()
