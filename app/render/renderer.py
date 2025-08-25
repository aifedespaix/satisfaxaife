from __future__ import annotations

import math
import os
import random
from dataclasses import dataclass, field

import numpy as np
import pygame

from app.core.config import settings
from app.core.types import Color, Vec2
from app.render.hud import Hud

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


@dataclass(slots=True)
class _BallState:
    prev_pos: Vec2 | None = None
    trail: list[tuple[Vec2, float]] = field(default_factory=list)
    blink_timer: int = field(default_factory=lambda: random.randint(60, 180))
    blink_progress: int = 0


@dataclass(slots=True)
class _Particle:
    pos: Vec2
    vel: Vec2


@dataclass(slots=True)
class _Impact:
    pos: Vec2
    timer: float
    particles: list[_Particle]


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
        self._impacts: list[_Impact] = []
        self._shake: Vec2 = (0.0, 0.0)
        self._hp_display = [1.0, 1.0]

    def clear(self) -> None:
        """Clear frame, update impacts and draw arena background."""
        self.surface.fill(self.background)
        self._update_impacts()
        margin = 20
        arena_rect = pygame.Rect(margin, margin, self.width - 2 * margin, self.height - 2 * margin)
        pygame.draw.rect(self.surface, self.arena_color, arena_rect, border_radius=30)

    def _update_impacts(self) -> None:
        self._shake = (0.0, 0.0)
        updated: list[_Impact] = []
        for impact in self._impacts:
            impact.timer -= settings.dt
            if impact.timer <= 0:
                continue
            for particle in impact.particles:
                particle.pos = (
                    particle.pos[0] + particle.vel[0] * settings.dt,
                    particle.pos[1] + particle.vel[1] * settings.dt,
                )
            strength = impact.timer / 0.08
            self._shake = (
                self._shake[0] + random.uniform(-1, 1) * strength,
                self._shake[1] + random.uniform(-1, 1) * strength,
            )
            updated.append(impact)
        self._impacts = updated

    def _get_state(self, key: Color) -> _BallState:
        return self._balls.setdefault(key, _BallState())

    def _draw_trail(self, state: _BallState, color: Color, radius: int) -> None:
        updated: list[tuple[Vec2, float]] = []
        for pos, alpha in state.trail:
            if alpha <= 10:
                continue
            trail_color = (*color, int(alpha))
            pygame.draw.circle(self.surface, trail_color, self._offset(pos), radius // 2)
            updated.append((pos, alpha * 0.7))
        state.trail = updated

    def _offset(self, pos: Vec2) -> Vec2:
        return (pos[0] + self._shake[0], pos[1] + self._shake[1])

    def add_impact(self, pos: Vec2) -> None:
        """Register an impact for visual feedback."""
        particles = []
        for _ in range(random.randint(6, 10)):
            ang = random.uniform(0, 2 * 3.14159)
            speed = random.uniform(80, 160)
            vel = (math.cos(ang) * speed, math.sin(ang) * speed)
            particles.append(_Particle(pos=pos, vel=vel))
        self._impacts.append(_Impact(pos=pos, timer=0.08, particles=particles))

    def update_hp(self, hp_a: float, hp_b: float) -> None:
        target = [hp_a, hp_b]
        for i, value in enumerate(target):
            diff = value - self._hp_display[i]
            step = settings.dt / 0.2
            self._hp_display[i] += diff * min(1.0, step)

    def draw_ball(self, pos: Vec2, radius: int, color: Color, team_color: Color) -> None:
        state = self._get_state(team_color)
        if state.prev_pos is not None:
            vx = pos[0] - state.prev_pos[0]
            vy = pos[1] - state.prev_pos[1]
            speed = (vx * vx + vy * vy) ** 0.5
            state.trail.append((pos, min(255.0, speed * 10.0)))
        state.prev_pos = pos
        self._draw_trail(state, team_color, radius)
        pygame.draw.circle(self.surface, color, self._offset(pos), radius)
        pygame.draw.circle(self.surface, team_color, self._offset(pos), radius + 3, width=3)
        highlight_pos = (pos[0] - radius * 0.3, pos[1] - radius * 0.3)
        pygame.draw.circle(
            self.surface, (255, 255, 255, 80), self._offset(highlight_pos), int(radius * 0.3)
        )

    def draw_projectile(self, pos: Vec2, radius: int, color: Color) -> None:
        pygame.draw.circle(self.surface, color, self._offset(pos), radius)

    def draw_eyes(self, pos: Vec2, gaze: Vec2, radius: int, team_color: Color) -> None:
        state = self._get_state(team_color)
        if state.blink_progress > 0:
            state.blink_progress -= 1
            left = (pos[0] - radius * 0.3, pos[1] - radius * 0.2)
            right = (pos[0] + radius * 0.3, pos[1] - radius * 0.2)
            pygame.draw.line(
                self.surface,
                (0, 0, 0),
                self._offset(left),
                self._offset((left[0] + radius * 0.2, left[1])),
                2,
            )
            pygame.draw.line(
                self.surface,
                (0, 0, 0),
                self._offset(right),
                self._offset((right[0] + radius * 0.2, right[1])),
                2,
            )
            return
        state.blink_timer -= 1
        if state.blink_timer <= 0:
            state.blink_timer = random.randint(60, 180)
            state.blink_progress = 5
        offset = (gaze[0] * radius * 0.3, gaze[1] * radius * 0.3)
        for dx in (-radius * 0.3, radius * 0.3):
            center = (pos[0] + dx + offset[0], pos[1] - radius * 0.2 + offset[1])
            pygame.draw.circle(self.surface, (0, 0, 0), self._offset(center), int(radius * 0.15))

    def trigger_blink(self, team_color: Color, strength: int) -> None:
        state = self._get_state(team_color)
        state.blink_progress = max(state.blink_progress, strength)

    def draw_impacts(self) -> None:
        for impact in self._impacts:
            alpha = int(255 * (impact.timer / 0.08))
            pygame.draw.circle(self.surface, (255, 255, 255, alpha), self._offset(impact.pos), 20)
            for particle in impact.particles:
                pygame.draw.circle(self.surface, (255, 180, 0), self._offset(particle.pos), 3)

    def draw_hp(self, surface: pygame.Surface, hud: Hud, labels: tuple[str, str]) -> None:
        hud.draw_hp_bars(surface, self._hp_display[0], self._hp_display[1], labels)

    def present(self) -> None:
        self.frame_index += 1

    def capture_frame(self) -> np.ndarray:
        array = pygame.surfarray.array3d(self.surface)
        return np.swapaxes(array, 0, 1)
