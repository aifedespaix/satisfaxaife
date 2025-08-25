from __future__ import annotations

import os
import random
from dataclasses import dataclass, field

import numpy as np
import pygame

from app.core.config import settings
from app.core.types import Color, Vec2

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@dataclass(slots=True)
class _BallState:
    """Visual state for a single ball."""

    prev_pos: Vec2 | None = None
    trail: list[tuple[Vec2, float]] = field(default_factory=list)
    blink_timer: int = field(default_factory=lambda: random.randint(60, 180))
    blink_progress: int = 0


class Renderer:
    """Off-screen renderer producing frames for the recorder."""

    def __init__(self, width: int = settings.width, height: int = settings.height) -> None:
        pygame.init()
        pygame.font.init()
        self.width = width
        self.height = height
        self.surface = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        self._balls: dict[Color, _BallState] = {}
        self.frame_index = 0
        self.background = (10, 10, 10)
        self.arena_color = (20, 20, 20)

    def clear(self) -> None:
        """Clear frame and draw arena background."""
        self.surface.fill(self.background)
        margin = 20
        arena_rect = pygame.Rect(margin, margin, self.width - 2 * margin, self.height - 2 * margin)
        pygame.draw.rect(self.surface, self.arena_color, arena_rect, border_radius=30)

    def _get_state(self, key: Color) -> _BallState:
        return self._balls.setdefault(key, _BallState())

    def _draw_trail(self, state: _BallState, color: Color, radius: int) -> None:
        updated: list[tuple[Vec2, float]] = []
        for pos, alpha in state.trail:
            if alpha <= 10:
                continue
            trail_color = (*color, int(alpha))
            pygame.draw.circle(self.surface, trail_color, pos, radius // 2)
            updated.append((pos, alpha * 0.7))
        state.trail = updated

    def draw_ball(self, pos: Vec2, radius: int, color: Color, team_color: Color) -> None:
        """Draw a ball with a team ring and glossy highlight."""
        state = self._get_state(team_color)
        if state.prev_pos is not None:
            vx = pos[0] - state.prev_pos[0]
            vy = pos[1] - state.prev_pos[1]
            speed = (vx * vx + vy * vy) ** 0.5
            state.trail.append((pos, min(255.0, speed * 10.0)))
        state.prev_pos = pos
        self._draw_trail(state, team_color, radius)
        pygame.draw.circle(self.surface, color, pos, radius)
        pygame.draw.circle(self.surface, team_color, pos, radius + 3, width=3)
        highlight_pos = (pos[0] - radius * 0.3, pos[1] - radius * 0.3)
        pygame.draw.circle(self.surface, (255, 255, 255, 80), highlight_pos, int(radius * 0.3))

    def draw_projectile(self, pos: Vec2, radius: int, color: Color) -> None:
        """Draw a simple projectile."""
        pygame.draw.circle(self.surface, color, pos, radius)

    def draw_eyes(self, pos: Vec2, gaze: Vec2, radius: int, team_color: Color) -> None:
        """Draw eyes with a blinking effect looking towards *gaze*."""
        state = self._get_state(team_color)
        if state.blink_progress > 0:
            state.blink_progress -= 1
            left = (pos[0] - radius * 0.3, pos[1] - radius * 0.2)
            right = (pos[0] + radius * 0.3, pos[1] - radius * 0.2)
            pygame.draw.line(self.surface, (0, 0, 0), left, (left[0] + radius * 0.2, left[1]), 2)
            pygame.draw.line(self.surface, (0, 0, 0), right, (right[0] + radius * 0.2, right[1]), 2)
            return
        state.blink_timer -= 1
        if state.blink_timer <= 0:
            state.blink_timer = random.randint(60, 180)
            state.blink_progress = 5
        offset = (gaze[0] * radius * 0.3, gaze[1] * radius * 0.3)
        for dx in (-radius * 0.3, radius * 0.3):
            center = (pos[0] + dx + offset[0], pos[1] - radius * 0.2 + offset[1])
            pygame.draw.circle(self.surface, (0, 0, 0), center, int(radius * 0.15))

    def present(self) -> None:
        """Advance frame counter."""
        self.frame_index += 1

    def capture_frame(self) -> np.ndarray:
        """Return the current frame as a NumPy array."""
        array = pygame.surfarray.array3d(self.surface)
        return np.swapaxes(array, 0, 1)
