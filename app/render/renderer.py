from __future__ import annotations

import math
import os
import random
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pygame

from app.core.config import settings
from app.core.types import Color, Vec2
from app.display import Display
from app.render.hud import Hud

# Angle quantization step for rotated sprite caching in degrees.
_ROTATION_STEP_DEGREES = 5

def draw_soft_light(
    surface: pygame.Surface,
    center: Vec2,
    radius: int,
    color: Color,
    max_alpha: int = 120,
) -> None:
    """Dessine une lumière douce avec un dégradé radial réel."""
    size = radius * 2
    glow = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = radius, radius

    for y in range(size):
        for x in range(size):
            dx = x - cx
            dy = y - cy
            dist = math.sqrt(dx * dx + dy * dy)
            if dist <= radius:
                alpha = int(max_alpha * (1 - dist / radius))
                glow.set_at((x, y), (*color, alpha))

    rect = glow.get_rect(center=center)
    surface.blit(glow, rect)


@dataclass(slots=True)
class _BallState:
    prev_pos: Vec2 | None = None
    trail: list[tuple[Vec2, float]] = field(default_factory=list)
    ghosts: list[_Ghost] = field(default_factory=list)
    blink_timer: int = field(default_factory=lambda: random.randint(60, 180))
    blink_progress: int = 0
    hit_flash_timer: float = 0.0
    hit_flash_duration: float = 0.0


@dataclass(slots=True)
class _Ghost:
    pos: Vec2
    alpha: float


@dataclass(slots=True)
class _Particle:
    pos: Vec2
    vel: Vec2


@dataclass(slots=True)
class _Impact:
    pos: Vec2
    timer: float
    duration: float
    particles: list[_Particle]
    scale: float = 1.0


class Renderer:
    """Render match frames, optionally displaying them in a window."""

    def __init__(
        self,
        width: int = settings.width,
        height: int = settings.height,
        display: bool = False,
        *,
        debug: bool = False,
    ) -> None:
        """Create a renderer.

        Args:
            width: Surface width in pixels.
            height: Surface height in pixels.
            display: Whether to show a window instead of rendering off-screen.
        """
        if not display:
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

        pygame.init()
        pygame.font.init()

        self.width = width
        self.height = height

        # ``convert_alpha`` requires an initialized display surface. Even in headless mode
        # a tiny hidden window is created so sprites can be loaded safely.
        self._display: Display | None
        if display:
            self._display = Display(width, height)
        else:
            pygame.display.set_mode((1, 1))
            self._display = None

        self.surface = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        self._balls: dict[Color, _BallState] = {}
        self.frame_index = 0
        self.background = (10, 10, 10)
        self.arena_color = (20, 20, 20)
        self._impacts: list[_Impact] = []
        self._shake: Vec2 = (0.0, 0.0)
        self._hp_display = [1.0, 1.0]
        self.debug = debug
        assets_dir = Path(__file__).resolve().parents[2] / "assets"
        self._ball_sprites: dict[Color, pygame.Surface] = {
            settings.theme.team_a.primary: pygame.image.load(
                assets_dir / "ball-a.png"
            ).convert_alpha(),
            settings.theme.team_b.primary: pygame.image.load(
                assets_dir / "ball-b.png"
            ).convert_alpha(),
        }
        self._scaled_ball_sprites: dict[tuple[Color, int], pygame.Surface] = {}
        self._rotation_cache: dict[tuple[pygame.Surface, int], pygame.Surface] = {}

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
            strength = (impact.timer / impact.duration) * impact.scale
            self._shake = (
                self._shake[0] + random.uniform(-1, 1) * strength,
                self._shake[1] + random.uniform(-1, 1) * strength,
            )
            updated.append(impact)
        self._impacts = updated

    def _get_state(self, key: Color) -> _BallState:
        return self._balls.setdefault(key, _BallState())

    def _draw_ghosts(self, state: _BallState, color: Color, radius: int) -> None:
        updated: list[_Ghost] = []
        for ghost in state.ghosts:
            if ghost.alpha <= 10:
                continue
            ghost_color = (*color, int(ghost.alpha))
            pygame.draw.circle(self.surface, ghost_color, self._offset(ghost.pos), radius)
            ghost.alpha *= 0.5
            updated.append(ghost)
        state.ghosts = updated

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

    def draw_line(self, start: Vec2, end: Vec2, color: Color, width: int = 1) -> None:
        """Draw a line between two points with camera shake applied."""
        pygame.draw.line(self.surface, color, self._offset(start), self._offset(end), width)

    def draw_circle_outline(self, pos: Vec2, radius: float, color: Color, width: int = 1) -> None:
        """Draw a circle outline centered at ``pos`` with ``radius`` pixels."""
        pygame.draw.circle(self.surface, color, self._offset(pos), int(radius), width)

    def draw_sprite(
        self,
        sprite: pygame.Surface,
        pos: Vec2,
        angle: float,
        aura_color: Color | None = None,
        aura_radius: int | None = None,
    ) -> None:
        """Render a rotated sprite centered at ``pos`` with an optional aura.

        Parameters
        ----------
        sprite:
            Image surface to draw.
        pos:
            Center position in world coordinates.
        angle:
            Rotation angle in radians.
        aura_color:
            Optional color for a concentric outline used to simulate a team aura.
        aura_radius:
            Radius of the aura circle in pixels. Required when ``aura_color`` is provided.
        """
        degrees = math.degrees(-angle)
        quantized = int(round(degrees / _ROTATION_STEP_DEGREES) * _ROTATION_STEP_DEGREES)
        quantized %= 360
        key = (sprite, quantized)
        rotated = self._rotation_cache.get(key)
        if rotated is None:
            rotated = pygame.transform.rotozoom(sprite, quantized, 1.0)
            self._rotation_cache[key] = rotated
        rect = rotated.get_rect(center=self._offset(pos))
        if aura_color is not None and aura_radius is not None:
            draw_soft_light(self.surface, rect.center, aura_radius, aura_color)
        self.surface.blit(rotated, rect)

    def add_impact(self, pos: Vec2, duration: float = 0.08) -> None:
        """Register an impact at ``pos`` lasting ``duration`` seconds.

        Parameters
        ----------
        pos:
            Impact position in world coordinates.
        duration:
            Lifetime of the impact in seconds. Defaults to ``0.08`` seconds.
        """
        if duration <= 0:
            raise ValueError("duration must be positive")

        # Longer durations imply stronger explosions (e.g., death).
        scale = 1.0 if duration <= 0.2 else min(3.0, 1.0 + (duration - 0.2) * 1.5)

        particles: list[_Particle] = []
        count = max(6, int(random.randint(8, 14) * scale))
        for _ in range(count):
            ang = random.uniform(0.0, 2.0 * math.pi)
            speed = random.uniform(80.0, 160.0) * scale
            vel = (math.cos(ang) * speed, math.sin(ang) * speed)
            particles.append(_Particle(pos=pos, vel=vel))
        self._impacts.append(
            _Impact(pos=pos, timer=duration, duration=duration, particles=particles, scale=scale)
        )

    def update_hp(self, hp_a: float, hp_b: float) -> None:
        target = [hp_a, hp_b]
        for i, value in enumerate(target):
            diff = value - self._hp_display[i]
            step = settings.dt / 0.2
            self._hp_display[i] += diff * min(1.0, step)

    def set_hp(self, hp_a: float, hp_b: float) -> None:
        """Immediately set health bar ratios.

        Parameters
        ----------
        hp_a : float
            Ratio for team A between 0 and 1.
        hp_b : float
            Ratio for team B between 0 and 1.
        """
        self._hp_display = [hp_a, hp_b]

    def draw_ball(
        self,
        pos: Vec2,
        radius: int,
        color: Color,
        team_color: Color,
        is_dashing: bool = False,
    ) -> None:
        """Draw the ball and update its trail.

        Parameters
        ----------
        pos:
            Ball position in world coordinates.
        radius:
            Ball radius in pixels.
        color:
            Fill color of the ball body.
        team_color:
            Outline color identifying the team.
        is_dashing:
            Whether the owning player is currently dashing. When ``True`` the
            trail effect is amplified by adding extra points and ghost clones
            are generated.
        """
        state = self._get_state(team_color)
        if is_dashing:
            state.ghosts.append(_Ghost(pos, 180.0))
        if state.prev_pos is not None:
            vx = pos[0] - state.prev_pos[0]
            vy = pos[1] - state.prev_pos[1]
            speed = (vx * vx + vy * vy) ** 0.5
            alpha = min(255.0, speed * 10.0)
            state.trail.append((pos, alpha))
            if is_dashing:
                # Add extra trail points to emphasize dash movement.
                for _ in range(2):
                    state.trail.append((pos, alpha))
        state.prev_pos = pos
        self._draw_ghosts(state, color, radius)
        self._draw_trail(state, team_color, radius)
        sprite = self._ball_sprites.get(team_color)
        if sprite is not None:
            diameter = radius * 2
            key = (team_color, diameter)
            cached = self._scaled_ball_sprites.get(key)
            if cached is None:
                if sprite.get_width() != diameter:
                    cached = pygame.transform.smoothscale(sprite, (diameter, diameter))
                else:
                    cached = sprite
                self._scaled_ball_sprites[key] = cached
            rect = cached.get_rect(center=self._offset(pos))
            self.surface.blit(cached, rect)
        else:
            pygame.draw.circle(self.surface, color, self._offset(pos), radius)
            pygame.draw.circle(self.surface, team_color, self._offset(pos), radius + 3, width=3)
            highlight_pos = (pos[0] - radius * 0.3, pos[1] - radius * 0.3)
            pygame.draw.circle(
                self.surface, (255, 255, 255, 80), self._offset(highlight_pos), int(radius * 0.3)
            )
        if state.hit_flash_timer > 0:
            strength = (
                state.hit_flash_timer / state.hit_flash_duration
                if state.hit_flash_duration > 0
                else 0.0
            )
            overlay = (255, 0, 0, int(255 * strength))
            pygame.draw.circle(self.surface, overlay, self._offset(pos), radius)
            state.hit_flash_timer = max(0.0, state.hit_flash_timer - settings.dt)

    def draw_projectile(
        self,
        pos: Vec2,
        radius: int,
        color: Color,
        aura_color: Color | None = None,
    ) -> None:
        """Draw a projectile centered at ``pos``.

        Parameters
        ----------
        pos:
            Center position of the projectile in world coordinates.
        radius:
            Projectile radius in pixels.
        color:
            Fill color of the projectile.
        aura_color:
            Optional color for a concentric outline used to simulate a team aura.
        """
        center = self._offset(pos)
        if aura_color is not None:
            draw_soft_light(self.surface, center, radius, aura_color)
        pygame.draw.circle(self.surface, color, center, radius)

    def draw_eyes(self, pos: Vec2, gaze: Vec2, radius: int, team_color: Color) -> None:
        if not settings.show_eyes:
            return
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
        sclera_radius = int(radius * 0.25)
        pupil_radius = int(radius * 0.12)
        max_offset = sclera_radius - pupil_radius
        for dx in (-radius * 0.3, radius * 0.3):
            sclera_center = (pos[0] + dx, pos[1] - radius * 0.2)
            pygame.draw.circle(
                self.surface, (255, 255, 255), self._offset(sclera_center), sclera_radius
            )
            pupil_center = (
                sclera_center[0] + gaze[0] * max_offset,
                sclera_center[1] + gaze[1] * max_offset,
            )
            pygame.draw.circle(self.surface, team_color, self._offset(pupil_center), pupil_radius)

    def trigger_blink(self, team_color: Color, strength: int) -> None:
        state = self._get_state(team_color)
        state.blink_progress = max(state.blink_progress, strength)

    def trigger_hit_flash(self, team_color: Color, duration: float = 0.15) -> None:
        """Flash the ball in red for ``duration`` seconds.

        Parameters
        ----------
        team_color:
            Team color identifying the target ball.
        duration:
            Duration of the flash in seconds. Defaults to ``0.15`` seconds.
        """
        if duration <= 0:
            raise ValueError("duration must be positive")
        state = self._get_state(team_color)
        state.hit_flash_timer = duration
        state.hit_flash_duration = duration

    def draw_impacts(self) -> None:
        for impact in self._impacts:
            alpha = int(255 * (impact.timer / impact.duration))
            radius = max(6, int(20 * impact.scale))
            pygame.draw.circle(
                self.surface, (255, 255, 255, alpha), self._offset(impact.pos), radius
            )
            pr = max(2, int(3 * impact.scale))
            for particle in impact.particles:
                pygame.draw.circle(self.surface, (255, 180, 0), self._offset(particle.pos), pr)

    def draw_hp(self, surface: pygame.Surface, hud: Hud, labels: tuple[str, str]) -> None:
        hud.draw_hp_bars(surface, self._hp_display[0], self._hp_display[1], labels)

    def present(self) -> None:
        """Advance to the next frame and update the display if enabled."""
        if self._display is not None:
            self._display.present(self.surface)
        self.frame_index += 1

    def capture_frame(self) -> np.ndarray:
        array = pygame.surfarray.array3d(self.surface)
        return np.swapaxes(array, 0, 1)
