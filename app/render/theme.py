from __future__ import annotations

from dataclasses import dataclass

import pygame

from app.core.types import Color


@dataclass(frozen=True)
class TeamColors:
    """Color definitions for a team."""

    primary: Color
    hp_gradient: tuple[Color, Color]


@dataclass(frozen=True)
class Theme:
    """Complete color palette for the renderer and HUD.

    Attributes
    ----------
    team_a:
        Colors for team A.
    team_b:
        Colors for team B.
    hp_empty:
        Color displayed for lost health.
    """

    team_a: TeamColors
    team_b: TeamColors
    hp_empty: Color


def draw_horizontal_gradient(
    surface: pygame.Surface,
    rect: pygame.Rect,
    start: Color,
    end: Color,
) -> None:
    """Draw a left-to-right linear gradient on the given surface."""

    for x in range(rect.width):
        ratio = x / rect.width
        r = int(start[0] + (end[0] - start[0]) * ratio)
        g = int(start[1] + (end[1] - start[1]) * ratio)
        b = int(start[2] + (end[2] - start[2]) * ratio)
        pygame.draw.line(
            surface,
            (r, g, b),
            (rect.x + x, rect.y),
            (rect.x + x, rect.y + rect.height),
        )
