from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

import numpy as np
import pygame

from app.ai.policy import SimplePolicy
from app.core.config import settings
from app.core.types import Color, Damage, EntityId, Vec2
from app.render.hud import Hud
from app.render.renderer import Renderer
from app.video.recorder import Recorder
from app.weapons import weapon_registry
from app.weapons.base import Weapon, WorldView
from app.world.entities import Ball
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


@dataclass(slots=True)
class Player:
    eid: EntityId
    ball: Ball
    weapon: Weapon
    policy: SimplePolicy
    face: Vec2
    color: Color
    alive: bool = True


class MatchTimeout(Exception):
    """Raised when a match exceeds the maximum duration."""


class _MatchView(WorldView):
    def __init__(
        self,
        players: list[Player],
        projectiles: list[Projectile],
        world: PhysicsWorld,
        renderer: Renderer,
    ) -> None:
        self.players = players
        self.projectiles = projectiles
        self.world = world
        self.renderer = renderer

    def get_enemy(self, owner: EntityId) -> EntityId | None:
        for p in self.players:
            if p.eid != owner and p.alive:
                return p.eid
        return None

    def get_position(self, eid: EntityId) -> Vec2:
        for p in self.players:
            if p.eid == eid:
                pos = p.ball.body.position
                return (float(pos.x), float(pos.y))
        for proj in self.projectiles:
            if proj.owner == eid:
                pos = proj.body.position
                return (float(pos.x), float(pos.y))
        raise KeyError(eid)

    def get_health_ratio(self, eid: EntityId) -> float:
        for p in self.players:
            if p.eid == eid:
                return p.ball.health / p.ball.stats.max_health
        raise KeyError(eid)

    def deal_damage(self, eid: EntityId, damage: Damage) -> None:
        for p in self.players:
            if p.eid == eid and p.alive:
                p.alive = not p.ball.take_damage(damage)
                self.renderer.add_impact(self.get_position(eid))
                self.renderer.trigger_blink(p.color, int(damage.amount))
                return

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:
        for p in self.players:
            if p.eid == eid:
                p.ball.body.apply_impulse_at_local_point((vx, vy))
                return

def spawn_projectile(
    self,
    owner: EntityId,
    position: Vec2,
    velocity: Vec2,
    radius: float,
    damage: Damage,
    knockback: float,
    ttl: float,
) -> None:
    proj = Projectile.spawn(
        self.world, owner, position, velocity, radius, damage, knockback, ttl
    )
    self.projectiles.append(proj)


def run_match(  # noqa: C901
    weapon_a: str,
    weapon_b: str,
    recorder: Recorder,
    renderer: Renderer | None = None,
    max_seconds: int = 120,
) -> EntityId | None:
    """Run a minimal match and record frames.

    Parameters
    ----------
    weapon_a : str
        Weapon used by team A.
    weapon_b : str
        Weapon used by team B.
    recorder : Recorder
        Recorder instance responsible for writing video frames.
    renderer : Renderer | None, optional
        Optional renderer instance. If ``None``, an off-screen renderer is created.
    max_seconds : int, optional
        Maximum duration of the match. Default is 120 seconds.

    Returns
    -------
    EntityId | None
        Winning entity identifier or ``None`` if no winner.

    Raises
    ------
    MatchTimeout
        If the match exceeds ``max_seconds`` without a winner.
    """
    world = PhysicsWorld()
    renderer = renderer or Renderer(settings.width, settings.height)
    hud = Hud(settings.theme)

    ball_a = Ball.spawn(world, (settings.width * 0.25, settings.height * 0.5))
    ball_b = Ball.spawn(world, (settings.width * 0.75, settings.height * 0.5))
    players = [
        Player(
            ball_a.eid,
            ball_a,
            weapon_registry.create(weapon_a),
            SimplePolicy("aggressive"),
            (1.0, 0.0),
            settings.theme.team_a.primary,
        ),
        Player(
            ball_b.eid,
            ball_b,
            weapon_registry.create(weapon_b),
            SimplePolicy("kiter"),
            (-1.0, 0.0),
            settings.theme.team_b.primary,
        ),
    ]
    projectiles: list[Projectile] = []
    view = _MatchView(players, projectiles, world, renderer)

    elapsed = 0.0
    winner: EntityId | None = None
    first_frame: pygame.Surface | None = None
    buffer: list[pygame.Surface] = []
    buffer_len = int(settings.end_screen.slowmo_duration * settings.fps)

    try:
        while len([p for p in players if p.alive]) >= 2 and elapsed < max_seconds:
            for p in players:
                if not p.alive:
                    continue
                accel, face, fire = p.policy.decide(p.eid, view)
                p.face = face
                p.ball.body.velocity = (
                    p.ball.body.velocity[0] + accel[0] * settings.dt,
                    p.ball.body.velocity[1] + accel[1] * settings.dt,
                )
                p.weapon.step(settings.dt)
                if fire:
                    p.weapon.trigger(p.eid, view, face)
                p.ball.cap_speed()

            for proj in list(projectiles):
                if not proj.step(settings.dt):
                    projectiles.remove(proj)
                    world.space.remove(proj.body, proj.shape)
                    continue
                for p in players:
                    if p.eid == proj.owner or not p.alive:
                        continue
                    pos_p = p.ball.body.position
                    pos_proj = proj.body.position
                    dx = pos_proj.x - pos_p.x
                    dy = pos_proj.y - pos_p.y
                    dist_sq = dx * dx + dy * dy
                    if dist_sq <= (proj.shape.radius + p.ball.shape.radius) ** 2:
                        view.deal_damage(p.eid, proj.damage)
                        norm = sqrt(dist_sq) or 1.0
                        view.apply_impulse(
                            p.eid, dx / norm * proj.knockback, dy / norm * proj.knockback
                        )
                        world.space.remove(proj.body, proj.shape)
                        projectiles.remove(proj)
                        break
            world.step(settings.dt)
            renderer.clear()
            for proj in projectiles:
                pos = (float(proj.body.position.x), float(proj.body.position.y))
                renderer.draw_projectile(pos, int(proj.shape.radius), (255, 255, 0))
            for p in players:
                if not p.alive:
                    continue
                pos = (float(p.ball.body.position.x), float(p.ball.body.position.y))
                radius = int(p.ball.shape.radius)
                renderer.draw_ball(pos, radius, settings.ball_color, p.color)
                vx, vy = p.ball.body.velocity
                speed = sqrt(vx * vx + vy * vy)
                gaze = (vx / speed, vy / speed) if speed else p.face
                renderer.draw_eyes(pos, gaze, radius, p.color)
            renderer.draw_impacts()
            renderer.update_hp(
                players[0].ball.health / players[0].ball.stats.max_health,
                players[1].ball.health / players[1].ball.stats.max_health,
            )
            hud.draw_title(renderer.surface, settings.hud.title)
            renderer.draw_hp(
                renderer.surface, hud, (weapon_a.capitalize(), weapon_b.capitalize())
            )
            hud.draw_watermark(renderer.surface, settings.hud.watermark)
            renderer.present()
            frame_surface = renderer.surface.copy()
            frame = pygame.surfarray.array3d(frame_surface)
            recorder.add_frame(np.swapaxes(frame, 0, 1))
            if first_frame is None:
                first_frame = frame_surface.copy()
            buffer.append(frame_surface)
            if len(buffer) > buffer_len:
                buffer.pop(0)

            alive = [p for p in players if p.alive]
            if len(alive) == 1:
                winner = alive[0].eid
                break

            elapsed += settings.dt

        if len([p for p in players if p.alive]) >= 2 and elapsed >= max_seconds:
            raise MatchTimeout(f"Match exceeded {max_seconds} seconds")

        if winner is not None and buffer:
            title = settings.end_screen.victory_text.format(
                team="A" if winner == players[0].eid else "B"
            )
            weapon_name = weapon_a if winner == players[0].eid else weapon_b
            subtitle = settings.end_screen.subtitle_text.format(weapon=weapon_name)
            banner_surface = buffer[-1].copy()
            hud.draw_victory_banner(banner_surface, title, subtitle)
            banner_frame = np.swapaxes(
                pygame.surfarray.array3d(banner_surface), 0, 1
            )
            freeze_frames = int(settings.end_screen.freeze_ms / 1000 * settings.fps)
            for _ in range(max(1, freeze_frames)):
                recorder.add_frame(banner_frame)

            slow_factor = settings.end_screen.slowmo
            repeat = max(1, int(1 / slow_factor))
            for surf in buffer:
                surf_copy = surf.copy()
                hud.draw_victory_banner(surf_copy, title, subtitle)
                arr = np.swapaxes(pygame.surfarray.array3d(surf_copy), 0, 1)
                for _ in range(repeat):
                    recorder.add_frame(arr)

            if first_frame is not None:
                start_arr = pygame.surfarray.array3d(first_frame)
                end_arr = pygame.surfarray.array3d(banner_surface)
                fade_frames = int(settings.end_screen.fade_ms / 1000 * settings.fps)
                for i in range(max(1, fade_frames)):
                    t = (i + 1) / fade_frames
                    blended = (end_arr * (1 - t) + start_arr * t).astype(np.uint8)
                    recorder.add_frame(np.swapaxes(blended, 0, 1))

        return winner
    finally:
        recorder.close()
