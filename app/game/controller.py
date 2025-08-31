from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from math import sqrt

import numpy as np
import pygame

from app.ai.policy import SimplePolicy
from app.audio import AudioEngine, BallAudio
from app.core.config import settings
from app.core.types import Color, Damage, EntityId, ProjectileInfo, Vec2
from app.intro import IntroManager
from app.render.hud import Hud
from app.render.renderer import Renderer
from app.video.recorder import RecorderProtocol
from app.video.slowmo import append_slowmo_ending
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
                ratio = p.ball.health / p.ball.stats.max_health
                return float(ratio)
        raise KeyError(eid)

    def deal_damage(self, eid: EntityId, damage: Damage, timestamp: float) -> None:
        """Apply ``damage`` to ``eid`` at ``timestamp``."""
        for p in self.players:
            if p.eid == eid and p.alive:
                pos = self.get_position(eid)
                p.alive = not p.ball.take_damage(damage)
                if p.alive:
                    self.renderer.add_impact(pos)
                    p.audio.on_hit(timestamp=timestamp)
                else:
                    self.renderer.add_impact(pos, duration=2.0)
                    p.audio.on_explode(timestamp=timestamp)
                    weapon_audio = getattr(p.weapon, "audio", None)
                    if weapon_audio is not None:
                        weapon_audio.stop_idle(timestamp)
                self.renderer.trigger_blink(p.color, int(damage.amount))
                self.renderer.trigger_hit_flash(p.color)
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


class Phase(Enum):
    INTRO = "intro"
    RUNNING = "running"
    FINISHED = "finished"


class GameController:
    """Coordinate the match flow across different phases."""

    def __init__(
        self,
        weapon_a: str,
        weapon_b: str,
        players: list[Player],
        world: PhysicsWorld,
        renderer: Renderer,
        hud: Hud,
        engine: AudioEngine,
        recorder: RecorderProtocol,
        intro_manager: IntroManager,
        *,
        max_seconds: int = 120,
        display: bool = False,
    ) -> None:
        self.weapon_a = weapon_a
        self.weapon_b = weapon_b
        self.players = players
        self.world = world
        self.renderer = renderer
        self.hud = hud
        self.engine = engine
        self.recorder = recorder
        self.intro_manager = intro_manager
        self.max_seconds = max_seconds
        self.display = display

        self.effects: list[WeaponEffect] = []
        self.view = _MatchView(players, self.effects, world, renderer, engine)
        self.phase = Phase.INTRO
        self.elapsed = 0.0
        self.winner: EntityId | None = None
        self.winner_weapon: str | None = None
        # Absolute timestamp (including intro) when the fatal hit occurred.
        self.death_ts: float | None = None

    def run(self) -> str | None:  # noqa: C901
        """Execute the match and return the winning weapon, if any."""
        intro_elapsed = 0.0
        try:
            if not self.display:
                self.engine.start_capture()
            labels = (self.weapon_a.capitalize(), self.weapon_b.capitalize())
            self.intro_manager.start()
            while not self.intro_manager.is_finished():
                self.intro_manager.update(settings.dt)
                self.renderer.clear()
                self.intro_manager.draw(self.renderer.surface, labels, self.hud)
                self.hud.draw_title(self.renderer.surface, settings.hud.title)
                self.hud.draw_watermark(self.renderer.surface, settings.hud.watermark)
                self.renderer.present()
                if not self.display:
                    frame_surface = self.renderer.surface.copy()
                    frame = pygame.surfarray.array3d(frame_surface)
                    self.recorder.add_frame(np.swapaxes(frame, 0, 1))
                intro_elapsed += settings.dt
            self.phase = Phase.RUNNING
            while (
                len([p for p in self.players if p.alive]) >= 2 and self.elapsed < self.max_seconds
            ):
                current_time = intro_elapsed + self.elapsed
                for p in self.players:
                    if not p.alive:
                        continue
                    accel, face, fire = p.policy.decide(p.eid, self.view, p.weapon.speed)
                    p.face = face
                    p.ball.body.velocity = (
                        p.ball.body.velocity[0] + accel[0] * settings.dt,
                        p.ball.body.velocity[1] + accel[1] * settings.dt,
                    )
                    p.weapon.step(settings.dt)
                    p.weapon.update(p.eid, self.view, settings.dt)
                    if fire:
                        p.weapon.trigger(p.eid, self.view, face)
                    p.ball.cap_speed()

                for eff in list(self.effects):
                    if not eff.step(settings.dt):
                        eff.destroy()
                        self.effects.remove(eff)
                        continue
                    if isinstance(eff, Projectile):
                        proj_pos = (
                            float(eff.body.position.x),
                            float(eff.body.position.y),
                        )
                        proj_rad = float(eff.shape.radius)
                        deflected = False
                        for other in self.effects:
                            if other is eff:
                                continue
                            collide = getattr(other, "collides", None)
                            if collide is None or not collide(self.view, proj_pos, proj_rad):
                                continue
                            reflector = getattr(other, "deflect_projectile", None)
                            if reflector is not None:
                                reflector(self.view, eff, current_time)
                                deflected = True
                                break
                        if deflected:
                            continue
                    for p in self.players:
                        if p.eid == eff.owner or not p.alive:
                            continue
                        pos = (
                            float(p.ball.body.position.x),
                            float(p.ball.body.position.y),
                        )
                        if eff.collides(self.view, pos, p.ball.shape.radius):
                            keep = eff.on_hit(self.view, p.eid, current_time)
                            if not keep:
                                eff.destroy()
                                self.effects.remove(eff)
                            break
                self.world.step(settings.dt)
                self.renderer.clear()
                for eff in self.effects:
                    eff.draw(self.renderer, self.view)
                for p in self.players:
                    if not p.alive:
                        continue
                    pos = (
                        float(p.ball.body.position.x),
                        float(p.ball.body.position.y),
                    )
                    radius = int(p.ball.shape.radius)
                    self.renderer.draw_ball(pos, radius, settings.ball_color, p.color)
                    vx, vy = p.ball.body.velocity
                    speed = sqrt(vx * vx + vy * vy)
                    gaze = (vx / speed, vy / speed) if speed else p.face
                    if settings.show_eyes:
                        self.renderer.draw_eyes(pos, gaze, radius, p.color)
                self.renderer.draw_impacts()
                self.renderer.update_hp(
                    self.players[0].ball.health / self.players[0].ball.stats.max_health,
                    self.players[1].ball.health / self.players[1].ball.stats.max_health,
                )
                self.hud.draw_title(self.renderer.surface, settings.hud.title)
                self.renderer.draw_hp(
                    self.renderer.surface,
                    self.hud,
                    (self.weapon_a.capitalize(), self.weapon_b.capitalize()),
                )
                self.hud.draw_watermark(self.renderer.surface, settings.hud.watermark)
                self.renderer.present()
                if not self.display:
                    frame_surface = self.renderer.surface.copy()
                    frame = pygame.surfarray.array3d(frame_surface)
                    self.recorder.add_frame(np.swapaxes(frame, 0, 1))

                alive = [p for p in self.players if p.alive]
                if len(alive) == 1:
                    self.winner = alive[0].eid
                    self.death_ts = current_time + settings.dt
                    break

                self.elapsed += settings.dt

            if self.winner is not None:
                for p in self.players:
                    weapon_audio = getattr(p.weapon, "audio", None)
                    if weapon_audio is not None:
                        weapon_audio.stop_idle(self.death_ts)
                for p in self.players:
                    p.ball.body.velocity = (0.0, 0.0)
                hp_a = max(
                    0.0,
                    self.players[0].ball.health / self.players[0].ball.stats.max_health,
                )
                hp_b = max(
                    0.0,
                    self.players[1].ball.health / self.players[1].ball.stats.max_health,
                )
                self.renderer.set_hp(hp_a, hp_b)
                win_p = next(p for p in self.players if p.eid == self.winner)
                lose_p = next(p for p in self.players if p.eid != self.winner)
                self.winner_weapon = (
                    self.weapon_a if self.winner == self.players[0].eid else self.weapon_b
                )
                shrink_frames = int(settings.end_screen.explosion_duration * settings.fps)
                win_pos = (
                    float(win_p.ball.body.position.x),
                    float(win_p.ball.body.position.y),
                )
                lose_pos = (
                    float(lose_p.ball.body.position.x),
                    float(lose_p.ball.body.position.y),
                )
                self.renderer.add_impact(lose_pos, duration=2.0)
                for frame_index in range(max(1, shrink_frames)):
                    if frame_index > 0 and frame_index % 4 == 0:
                        self.renderer.add_impact(lose_pos, duration=2.0)
                    progress = (frame_index + 1) / max(1, shrink_frames)
                    self.renderer.clear()
                    lose_radius = int(lose_p.ball.shape.radius * (1.0 - progress))
                    if lose_radius > 0:
                        self.renderer.draw_ball(
                            lose_pos, lose_radius, settings.ball_color, lose_p.color
                        )
                    win_radius = int(win_p.ball.shape.radius)
                    self.renderer.draw_ball(win_pos, win_radius, settings.ball_color, win_p.color)
                    if settings.show_eyes:
                        self.renderer.draw_eyes(win_pos, win_p.face, win_radius, win_p.color)
                    self.renderer.draw_impacts()
                    self.renderer.draw_hp(
                        self.renderer.surface,
                        self.hud,
                        (self.weapon_a.capitalize(), self.weapon_b.capitalize()),
                    )
                    self.hud.draw_title(self.renderer.surface, settings.hud.title)
                    self.hud.draw_watermark(self.renderer.surface, settings.hud.watermark)
                    self.renderer.present()
                    if not self.display:
                        frame_surface = self.renderer.surface.copy()
                        self.recorder.add_frame(
                            np.swapaxes(pygame.surfarray.array3d(frame_surface), 0, 1)
                        )
                self.phase = Phase.FINISHED
                return self.winner_weapon

            if len([p for p in self.players if p.alive]) >= 2 and self.elapsed >= self.max_seconds:
                raise MatchTimeout(f"Match exceeded {self.max_seconds} seconds")
            self.phase = Phase.FINISHED
            return self.winner_weapon
        finally:
            for player in self.players:
                weapon_audio = getattr(player.weapon, "audio", None)
                if weapon_audio is not None:
                    weapon_audio.stop_idle(None)
            audio = self.engine.end_capture() if not self.display else None
            self.engine.stop_all()
            self.recorder.close(audio)
            if not self.display and self.death_ts is not None and self.recorder.path is not None:
                append_slowmo_ending(
                    self.recorder.path,
                    self.death_ts,
                    settings.end_screen.pre_s,
                    settings.end_screen.post_s,
                    settings.end_screen.slow_factor,
                    intro_elapsed,
                )
            self.engine.shutdown()
