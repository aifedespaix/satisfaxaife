from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import sqrt

import numpy as np
import pygame

from app.ai.policy import SimplePolicy
from app.audio import AudioEngine, BallAudio, get_default_engine
from app.core.config import settings
from app.core.types import Color, Damage, EntityId, ProjectileInfo, Vec2
from app.render.hud import Hud
from app.render.renderer import Renderer
from app.video.recorder import Recorder
from app.weapons import weapon_registry
from app.weapons.base import Weapon, WeaponEffect, WorldView
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
    audio: BallAudio
    alive: bool = True


class MatchTimeout(Exception):
    """Raised when a match exceeds the maximum duration."""


class _MatchView(WorldView):
    def __init__(
        self,
        players: list[Player],
        effects: list[WeaponEffect],
        world: PhysicsWorld,
        renderer: Renderer,
        engine: AudioEngine,
    ) -> None:
        self.players = players
        self.effects = effects
        self.world = world
        self.renderer = renderer
        self.engine = engine

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
        raise KeyError(eid)

    def get_velocity(self, eid: EntityId) -> Vec2:
        for p in self.players:
            if p.eid == eid:
                vel = p.ball.body.velocity
                return (float(vel.x), float(vel.y))
        raise KeyError(eid)

    def get_health_ratio(self, eid: EntityId) -> float:
        for p in self.players:
            if p.eid == eid:
                return p.ball.health / p.ball.stats.max_health
        raise KeyError(eid)

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:
        """Apply ``damage`` to ``eid`` at the given ``timestamp``."""
        for p in self.players:
            if p.eid == eid and p.alive:
                pos = self.get_position(eid)
                p.alive = not p.ball.take_damage(damage)
                if p.alive:
                    self.renderer.add_impact(pos)
                else:
                    self.renderer.add_impact(pos, duration=2.0)
                    p.audio.on_explode(timestamp=timestamp)
                    # Stop the weapon's idle audio thread when the player dies.
                    weapon_audio = getattr(p.weapon, "audio", None)
                    if weapon_audio is not None:
                        weapon_audio.stop_idle(timestamp)
                self.renderer.trigger_blink(p.color, int(damage.amount))
                return

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:
        for p in self.players:
            if p.eid == eid:
                p.ball.body.apply_impulse_at_local_point((vx, vy))
                return

    def spawn_effect(self, effect: WeaponEffect) -> None:
        self.effects.append(effect)

    def spawn_projectile(
        self,
        owner: EntityId,
        position: Vec2,
        velocity: Vec2,
        radius: float,
        damage: Damage,
        knockback: float,
        ttl: float,
        sprite: pygame.Surface | None = None,
        spin: float = 0.0,
    ) -> WeaponEffect:
        proj = Projectile.spawn(
            self.world,
            owner,
            position,
            velocity,
            radius,
            damage,
            knockback,
            ttl,
            sprite,
            spin,
        )
        self.effects.append(proj)
        return proj

    def iter_projectiles(self, excluding: EntityId | None = None) -> Iterable[ProjectileInfo]:
        for eff in self.effects:
            if isinstance(eff, Projectile) and eff.owner != excluding:
                pos = (float(eff.body.position.x), float(eff.body.position.y))
                vel = (float(eff.body.velocity.x), float(eff.body.velocity.y))
                yield ProjectileInfo(eff.owner, pos, vel)


def _append_slowmo_segment(audio: np.ndarray, engine: AudioEngine, death_ts: float) -> np.ndarray:
    """Append a slowed replay segment to ``audio``.

    Parameters
    ----------
    audio:
        Captured audio buffer.
    engine:
        Audio engine providing the resampling routine.
    death_ts:
        Timestamp of the kill event in seconds.

    Returns
    -------
    np.ndarray
        Audio buffer extended with the slow-motion replay segment.

    Raises
    ------
    ValueError
        If the window around ``death_ts`` contains no samples.
    """
    start = max(0, int((death_ts - settings.end_screen.slowmo_duration) * AudioEngine.SAMPLE_RATE))
    end = min(
        audio.shape[0],
        int((death_ts + settings.end_screen.explosion_duration) * AudioEngine.SAMPLE_RATE),
    )
    segment = audio[start:end]
    if segment.size == 0:
        msg = "Slow-motion window around death timestamp is empty"
        raise ValueError(msg)
    pad_samples = int(settings.end_screen.pre_slowmo_ms / 1000 * AudioEngine.SAMPLE_RATE)
    padded = np.concatenate([audio, np.zeros((pad_samples, audio.shape[1]), dtype=np.int16)])
    slowed = engine._resample(segment, settings.end_screen.slowmo)
    return np.concatenate([padded, slowed])


def run_match(  # noqa: C901
    weapon_a: str,
    weapon_b: str,
    recorder: Recorder,
    renderer: Renderer | None = None,
    max_seconds: int = 120,
) -> str | None:
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
    str | None
        Winning weapon name or ``None`` if no winner.

    Raises
    ------
    MatchTimeout
        If the match exceeds ``max_seconds`` without a winner.
    """
    engine = get_default_engine()
    engine.start_capture()
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
            BallAudio(engine=engine),
        ),
        Player(
            ball_b.eid,
            ball_b,
            weapon_registry.create(weapon_b),
            SimplePolicy("kiter"),
            (-1.0, 0.0),
            settings.theme.team_b.primary,
            BallAudio(engine=engine),
        ),
    ]
    effects: list[WeaponEffect] = []
    view = _MatchView(players, effects, world, renderer, engine)

    elapsed = 0.0
    winner: EntityId | None = None
    winner_weapon: str | None = None
    first_frame: pygame.Surface | None = None
    buffer: list[pygame.Surface] = []
    buffer_len = int(
        (settings.end_screen.slowmo_duration + settings.end_screen.explosion_duration)
        * settings.fps
    )
    death_ts: float | None = None

    try:
        while len([p for p in players if p.alive]) >= 2 and elapsed < max_seconds:
            for p in players:
                if not p.alive:
                    continue
                accel, face, fire = p.policy.decide(p.eid, view, p.weapon.speed)
                p.face = face
                p.ball.body.velocity = (
                    p.ball.body.velocity[0] + accel[0] * settings.dt,
                    p.ball.body.velocity[1] + accel[1] * settings.dt,
                )
                p.weapon.step(settings.dt)
                p.weapon.update(p.eid, view, settings.dt)
                if fire:
                    p.weapon.trigger(p.eid, view, face)
                p.ball.cap_speed()

            for eff in list(effects):
                if not eff.step(settings.dt):
                    eff.destroy()
                    effects.remove(eff)
                    continue
                if isinstance(eff, Projectile):
                    proj_pos = (float(eff.body.position.x), float(eff.body.position.y))
                    proj_rad = float(eff.shape.radius)
                    deflected = False
                    for other in effects:
                        if other is eff:
                            continue
                        collide = getattr(other, "collides", None)
                        if collide is None or not collide(view, proj_pos, proj_rad):
                            continue
                        reflector = getattr(other, "deflect_projectile", None)
                        if reflector is not None:
                            reflector(view, eff, elapsed)
                            deflected = True
                            break
                    if deflected:
                        continue
                for p in players:
                    if p.eid == eff.owner or not p.alive:
                        continue
                    pos = (float(p.ball.body.position.x), float(p.ball.body.position.y))
                    if eff.collides(view, pos, p.ball.shape.radius):
                        keep = eff.on_hit(view, p.eid, elapsed)
                        if not keep:
                            eff.destroy()
                            effects.remove(eff)
                        break
            world.step(settings.dt)
            renderer.clear()
            for eff in effects:
                eff.draw(renderer, view)
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
            renderer.draw_hp(renderer.surface, hud, (weapon_a.capitalize(), weapon_b.capitalize()))
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
                death_ts = elapsed + settings.dt
                break

            elapsed += settings.dt

        if winner is not None:
            for p in players:
                weapon_audio = getattr(p.weapon, "audio", None)
                if weapon_audio is not None:
                    weapon_audio.stop_idle(death_ts)
            for p in players:
                p.ball.body.velocity = (0.0, 0.0)
            hp_a = max(0.0, players[0].ball.health / players[0].ball.stats.max_health)
            hp_b = max(0.0, players[1].ball.health / players[1].ball.stats.max_health)
            renderer.set_hp(hp_a, hp_b)
            win_p = next(p for p in players if p.eid == winner)
            lose_p = next(p for p in players if p.eid != winner)
            winner_weapon = weapon_a if winner == players[0].eid else weapon_b
            shrink_frames = int(settings.end_screen.explosion_duration * settings.fps)
            win_pos = (
                float(win_p.ball.body.position.x),
                float(win_p.ball.body.position.y),
            )
            lose_pos = (
                float(lose_p.ball.body.position.x),
                float(lose_p.ball.body.position.y),
            )
            renderer.add_impact(lose_pos, duration=2.0)
            for frame_index in range(max(1, shrink_frames)):
                if frame_index > 0 and frame_index % 4 == 0:
                    renderer.add_impact(lose_pos, duration=2.0)
                progress = (frame_index + 1) / max(1, shrink_frames)
                renderer.clear()
                lose_radius = int(lose_p.ball.shape.radius * (1.0 - progress))
                if lose_radius > 0:
                    renderer.draw_ball(lose_pos, lose_radius, settings.ball_color, lose_p.color)
                win_radius = int(win_p.ball.shape.radius)
                renderer.draw_ball(win_pos, win_radius, settings.ball_color, win_p.color)
                renderer.draw_eyes(win_pos, win_p.face, win_radius, win_p.color)
                renderer.draw_impacts()
                renderer.draw_hp(
                    renderer.surface,
                    hud,
                    (weapon_a.capitalize(), weapon_b.capitalize()),
                )
                hud.draw_title(renderer.surface, settings.hud.title)
                hud.draw_watermark(renderer.surface, settings.hud.watermark)
                renderer.present()
                frame_surface = renderer.surface.copy()
                recorder.add_frame(np.swapaxes(pygame.surfarray.array3d(frame_surface), 0, 1))
                buffer.append(frame_surface)
                if len(buffer) > buffer_len:
                    buffer.pop(0)

            if buffer:
                title = settings.end_screen.victory_text.format(weapon=winner_weapon.capitalize())
                subtitle = settings.end_screen.subtitle_text.format(
                    weapon=winner_weapon.capitalize()
                )
                banner_surface = buffer[-1].copy()
                hud.draw_victory_banner(banner_surface, title, subtitle)
                banner_frame = np.swapaxes(pygame.surfarray.array3d(banner_surface), 0, 1)
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

            return winner_weapon

        if len([p for p in players if p.alive]) >= 2 and elapsed >= max_seconds:
            raise MatchTimeout(f"Match exceeded {max_seconds} seconds")

        return winner_weapon
    finally:
        # Ensure all weapon idle sounds stop when the match concludes.
        for player in players:
            weapon_audio = getattr(player.weapon, "audio", None)
            if weapon_audio is not None:
                weapon_audio.stop_idle(None)
        audio = engine.end_capture()
        if death_ts is not None:
            audio = _append_slowmo_segment(audio, engine, death_ts)
        engine.stop_all()
        recorder.close(audio)
        engine.shutdown()
