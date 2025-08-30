from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pygame

from app.core.types import Color


@dataclass(frozen=True)
class TeamColors:
    """Color definitions for a team."""

    primary: Color
    hp_gradient: tuple[Color, ...]


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
    hp_warning:
        Color used when a player is in the danger zone.
    """

    team_a: TeamColors
    team_b: TeamColors
    hp_empty: Color
    hp_warning: Color


def draw_horizontal_gradient(
    surface: pygame.Surface,
    rect: pygame.Rect,
    colors: Sequence[Color],
    phase: float = 0.0,
) -> None:
    """Draw a left-to-right linear gradient on the given surface.

    Parameters
    ----------
    surface:
        Target drawing surface.
    rect:
        Area where the gradient is rendered.
    colors:
        Sequence of colors defining the gradient stops. A single color
        fills ``rect`` uniformly.
    phase:
        Normalized offset applied to the gradient. ``0`` renders the
        gradient in its original position while values in ``[0, 1)`` shift
        it horizontally and wrap around. Animating ``phase`` with a
        ping-pong pattern (``0 → 1 → 0``) produces a smooth back-and-forth
        motion.
    """

    if not colors:
        return
    if len(colors) == 1:
        pygame.draw.rect(surface, colors[0], rect)
        return

    segments = len(colors) - 1
    for x in range(rect.width):
        t = (x / rect.width + phase) % 1.0
        pos = t * segments
        index = min(int(pos), segments - 1)
        ratio = pos - index
        start = colors[index]
        end = colors[index + 1]
        r = int(start[0] + (end[0] - start[0]) * ratio)
        g = int(start[1] + (end[1] - start[1]) * ratio)
        b = int(start[2] + (end[2] - start[2]) * ratio)
        pygame.draw.line(
            surface,
            (r, g, b),
            (rect.x + x, rect.y),
            (rect.x + x, rect.y + rect.height),
        )


def draw_diagonal_gradient(
    surface: pygame.Surface,
    rect: pygame.Rect,
    colors: Sequence[Color],
) -> None:
    """Draw a 45° gradient from the top-left to the bottom-right corner.

    Parameters
    ----------
    surface:
        Target drawing surface.
    rect:
        Area where the gradient is rendered.
    colors:
        Sequence of colors defining the gradient stops. A single color fills
        ``rect`` uniformly.
    """

    if not colors:
        return
    if len(colors) == 1:
        pygame.draw.rect(surface, colors[0], rect)
        return

    segments = len(colors) - 1
    max_dist = rect.width + rect.height
    for y in range(rect.height):
        for x in range(rect.width):
            t = (x + y) / max_dist
            pos = t * segments
            index = min(int(pos), segments - 1)
            ratio = pos - index
            start = colors[index]
            end = colors[index + 1]
            r = int(start[0] + (end[0] - start[0]) * ratio)
            g = int(start[1] + (end[1] - start[1]) * ratio)
            b = int(start[2] + (end[2] - start[2]) * ratio)
            surface.set_at((rect.x + x, rect.y + y), (r, g, b))
