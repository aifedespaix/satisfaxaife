"""Application settings loaded from a JSON file."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from pydantic import BaseModel

from app.core.types import Color
from app.render.theme import TeamColors, Theme


class Canvas(BaseModel):  # type: ignore[misc]
    """Video canvas configuration."""

    width: int = 1080
    height: int = 1920
    fps: int = 60

    @property
    def dt(self) -> float:
        return 1.0 / float(self.fps)


class HudConfig(BaseModel):  # type: ignore[misc]
    """Texts displayed in the HUD."""

    title: str = "Battle Balls"
    watermark: str = "@battleballs"


class EndScreenConfig(BaseModel):  # type: ignore[misc]
    """End screen behavior and texts."""

    victory_text: str = "Victory : {weapon}"
    subtitle_text: str = "{weapon} remporte le duel !"
    explosion_duration: float = 2.0


class Settings(BaseModel):  # type: ignore[misc]
    """Application configuration container."""

    canvas: Canvas = Canvas()
    theme: Theme = Theme(
        team_a=TeamColors(primary=(0, 102, 204), hp_gradient=((102, 178, 255), (0, 51, 102))),
        team_b=TeamColors(primary=(255, 102, 0), hp_gradient=((255, 178, 102), (102, 51, 0))),
        hp_empty=(51, 51, 51),
    )
    hud: HudConfig = HudConfig()
    end_screen: EndScreenConfig = EndScreenConfig()
    wall_thickness: int = 10
    background_color: Color = (30, 30, 30)
    ball_color: Color = (220, 220, 220)

    @property
    def width(self) -> int:
        return self.canvas.width

    @property
    def height(self) -> int:
        return self.canvas.height

    @property
    def fps(self) -> int:
        return self.canvas.fps

    @property
    def dt(self) -> float:
        return self.canvas.dt


def load_settings(path: Path | None = None) -> Settings:
    """Load settings from ``path`` or return defaults."""

    path = path or Path(__file__).with_name("config.json")
    if path.exists():
        data = json.loads(path.read_text())
        return cast(Settings, Settings.model_validate(data))
    return Settings()


settings = load_settings()
