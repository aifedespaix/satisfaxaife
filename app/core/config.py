from __future__ import annotations

from pydantic_settings import BaseSettings

from app.core.types import Color


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    width: int = 1080
    height: int = 1920
    fps: int = 60
    wall_thickness: int = 10
    background_color: Color = (30, 30, 30)
    ball_color: Color = (220, 220, 220)

    @property
    def dt(self) -> float:
        """Duration of a single frame in seconds."""
        return 1.0 / float(self.fps)


settings = Settings()
