from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from math import sqrt
from pathlib import Path

import numpy as np
import pygame

from app.ai.stateful_policy import StatefulPolicy
from app.audio import AudioEngine, BallAudio
from app.core.config import settings
from app.core.types import Color, Damage, EntityId, ProjectileInfo, Vec2
from app.game.dash import RANGED_COOLDOWN_FACTOR, Dash
from app.intro import IntroManager
from app.render.hud import Hud
from app.render.renderer import Renderer
from app.video.recorder import RecorderProtocol
from app.video.slowmo import append_slowmo_ending
from app.weapons.base import RangeType, Weapon, WeaponEffect, WorldView
from app.world.entities import Ball
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile
from pymunk import Vec2 as Vec2d

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DASH_SOUND_PATH = Path("assets/dash.ogg").as_posix()


@dataclass(slots=True)
class Player:
    eid: EntityId
    ball: Ball
    weapon: Weapon
    policy: StatefulPolicy
    face: Vec2
    color: Color
    audio: BallAudio
    dash: Dash = field(default_factory=Dash)
    alive: bool = True

    def __post_init__(self) -> None:
        """Adjust dash cooldown according to the weapon's range."""
        range_type: RangeType = getattr(self.weapon, "range_type", "contact")
        if range_type == "distant":
            self.dash.cooldown *= RANGED_COOLDOWN_FACTOR


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

    def get_team_color(self, eid: EntityId) -> Color:
        for p in self.players:
            if p.eid == eid:
                return p.color
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
                    for other in self.players:
                        weapon_audio = getattr(other.weapon, "audio", None)
                        if weapon_audio is not None:
                            weapon_audio.stop_idle(timestamp, disable=True)
                self.renderer.trigger_blink(p.color, int(damage.amount))
                self.renderer.trigger_hit_flash(p.color)
                return

    def apply_impulse(self, eid: EntityId, vx: float, vy: float) -> None:
        """Apply a physics impulse to ``eid``'s body.

        Parameters
        ----------
        eid:
            Identifier of the target entity.
        vx, vy:
            Components of the impulse vector.

        Raises
        ------
        KeyError
            If no player with ``eid`` exists.
        """
        for p in self.players:
            if p.eid == eid:
                p.ball.body.apply_impulse_at_local_point((vx, vy))
                return
        raise KeyError(eid)

    def add_speed_bonus(self, eid: EntityId, bonus: float) -> None:
        for p in self.players:
            if p.eid == eid:
                p.ball.stats.max_speed += bonus
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
        trail_color: Color | None = None,
        acceleration: float = 0.0,
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
            trail_color,
            acceleration,
        )
        self.effects.append(proj)
        return proj

    def iter_projectiles(self, excluding: EntityId | None = None) -> Iterable[ProjectileInfo]:
        for eff in self.effects:
            if isinstance(eff, Projectile) and eff.owner != excluding:
                pos = (float(eff.body.position.x), float(eff.body.position.y))
                vel = (float(eff.body.velocity.x), float(eff.body.velocity.y))
                yield ProjectileInfo(eff.owner, pos, vel)

    def get_weapon(self, eid: EntityId) -> Weapon:
        for p in self.players:
            if p.eid == eid:
                return p.weapon
        raise KeyError(eid)


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
        ai_transition_seconds: int = 20,
    ) -> None:
        """Initialise the controller.

        Parameters
        ----------
        weapon_a, weapon_b:
            Names of the weapons used by the two players.
        players:
            Active players taking part in the match.
        world:
            Physics world where the simulation occurs.
        renderer:
            Renderer used to draw frames.
        hud:
            Heads-up display renderer.
        engine:
            Audio engine responsible for playing sounds.
        recorder:
            Recorder receiving rendered frames.
        intro_manager:
            Manager for the intro sequence shown before the match.
        max_seconds:
            Maximum match duration.
        display:
            When ``True`` render to the screen instead of recording.
        ai_transition_seconds:
            Delay before switching to advanced AI behaviour.
        """
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
        self.ai_transition_seconds = ai_transition_seconds

        self.effects: list[WeaponEffect] = []
        self.view = _MatchView(players, self.effects, world, renderer, engine)
        self.world.set_projectile_removed_callback(self._on_projectile_removed)
        self.phase = Phase.INTRO
        self.elapsed = 0.0
        self._next_log_second = 1
        self.winner: EntityId | None = None
        self.winner_weapon: str | None = None
        # Absolute timestamp (including intro) when the fatal hit occurred.
        self.death_ts: float | None = None
        self.labels = (self.weapon_a.capitalize(), self.weapon_b.capitalize())

    def run(self) -> str | None:
        """Execute the match and return the winning weapon, if any."""
        intro_elapsed = 0.0
        try:
            if not self.display:
                self.engine.start_capture()
            ball_positions: tuple[Vec2, Vec2] = (
                (
                    float(self.players[0].ball.body.position.x),
                    float(self.players[0].ball.body.position.y),
                ),
                (
                    float(self.players[1].ball.body.position.x),
                    float(self.players[1].ball.body.position.y),
                ),
            )
            intro_elapsed = self._run_intro(ball_positions)
            self.phase = Phase.RUNNING
            self._run_match_loop(intro_elapsed)
            return self.winner_weapon
        finally:
            self._teardown(intro_elapsed)

    def get_winner_health_ratio(self) -> float | None:
        """Return remaining health ratio of the winning player.

        The ratio is expressed between 0.0 and 1.0. ``None`` is returned if the
        match ended without a winner or if the winner cannot be determined.
        """
        if self.winner is None:
            return None
        for player in self.players:
            if player.eid == self.winner:
                return float(player.ball.health / player.ball.stats.max_health)
        return None

    def _run_intro(self, ball_positions: tuple[Vec2, Vec2]) -> float:
        """Play the intro sequence and return its duration."""
        intro_elapsed = 0.0
        self.intro_manager.start()
        while not self.intro_manager.is_finished():
            self.intro_manager.update(settings.dt)
            self.renderer.clear()
            self.intro_manager.draw(self.renderer.surface, self.labels, self.hud, ball_positions)
            self.hud.draw_title(self.renderer.surface, settings.hud.title)
            self.hud.draw_watermark(self.renderer.surface, settings.hud.watermark)
            self.renderer.present()
            self._capture_frame()
            intro_elapsed += settings.dt
        return intro_elapsed

    def _run_match_loop(self, intro_elapsed: float) -> None:
        """Run the core match loop until a winner or timeout."""
        while len([p for p in self.players if p.alive]) >= 2 and self.elapsed < self.max_seconds:
            current_time = intro_elapsed + self.elapsed
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_LSHIFT:
                    self.players[0].dash.start(self.players[0].face, current_time)
            self._update_players(current_time)
            self._step_effects()
            self._deflect_projectiles(current_time)
            self.world.set_context(self.view, current_time)
            self.world.step(settings.dt, settings.physics_substeps)
            for p in self.players:
                if p.alive:
                    self._resolve_dash_collision(p, current_time)
            self._resolve_effect_hits(current_time)
            self._render_frame()
            self._capture_frame()

            alive = [p for p in self.players if p.alive]
            if len(alive) == 1:
                self.winner = alive[0].eid
                self.death_ts = current_time + settings.dt
                break

            self.elapsed += settings.dt
            if self.elapsed >= self._next_log_second:
                logger.info("Simulation time: %d s", self._next_log_second)
                self._next_log_second += 1

        if self.winner is not None:
            self._play_winner_sequence()
            return
        if len([p for p in self.players if p.alive]) >= 2 and self.elapsed >= self.max_seconds:
            raise MatchTimeout(f"Match exceeded {self.max_seconds} seconds")
        self.phase = Phase.FINISHED

    def _update_players(self, now: float) -> None:
        """Update player positions, dash and weapon state."""
        for p in self.players:
            if not p.alive:
                continue
            accel, face, fire = p.policy.decide(p.eid, self.view, now, p.weapon.speed)
            dash_dir = p.policy.dash_direction(p.eid, self.view, now, p.dash.can_dash)
            p.face = face
            if dash_dir is not None:
                was_dashing = p.dash.is_dashing
                p.dash.start(dash_dir, now)
                if not was_dashing and p.dash.is_dashing:
                    self.engine.play_variation(DASH_SOUND_PATH, timestamp=now)
            p.dash.update(now)
            new_velocity = p.ball.body.velocity + Vec2d(
                accel[0] * settings.dt,
                accel[1] * settings.dt,
            )
            if p.dash.is_dashing:
                new_velocity = Vec2d(
                    p.dash.direction[0] * p.dash.speed,
                    p.dash.direction[1] * p.dash.speed,
                )
            p.ball.body.velocity = new_velocity
            p.weapon.step(settings.dt)
            p.weapon.update(p.eid, self.view, settings.dt)
            if fire:
                p.weapon.trigger(p.eid, self.view, face)
            p.ball.cap_speed()

    def _resolve_dash_collision(self, p: Player, now: float) -> None:
        """Resolve dash impacts between ``p`` and opponents."""
        if not p.dash.is_dashing or p.dash.has_hit:
            return
        pa = p.ball.body.position
        for other in self.players:
            if other.eid == p.eid or not other.alive:
                continue
            pb = other.ball.body.position
            radii = float(p.ball.shape.radius + other.ball.shape.radius)
            dx = pb.x - pa.x
            dy = pb.y - pa.y
            if dx * dx + dy * dy > radii * radii:
                continue
            self.view.apply_impulse(
                other.eid,
                p.dash.direction[0] * p.dash.knockback,
                p.dash.direction[1] * p.dash.knockback,
            )
            vx, vy = p.ball.body.velocity
            speed = sqrt(vx * vx + vy * vy)
            scaled = Damage(p.dash.damage.amount * speed / p.dash.speed)
            self.view.deal_damage(other.eid, scaled, now)
            p.dash.has_hit = True
            return

    def _step_effects(self) -> None:
        """Advance effect state and prune expired entries."""
        for eff in list(self.effects):
            if not eff.step(settings.dt):
                eff.destroy()
                self.effects.remove(eff)

    def _deflect_projectiles(self, current_time: float) -> None:
        """Deflect active projectiles using defensive effects."""
        for eff in list(self.effects):
            if isinstance(eff, Projectile):
                self._deflect_projectile(eff, current_time)

    def _resolve_effect_hits(self, current_time: float) -> None:
        """Apply non-projectile effect collisions to players."""
        for eff in list(self.effects):
            if isinstance(eff, Projectile):
                continue
            owner = getattr(eff, "owner", None)
            for p in self.players:
                if p.eid == owner or not p.alive:
                    continue
                pos = (
                    float(p.ball.body.position.x),
                    float(p.ball.body.position.y),
                )
                radius = float(p.ball.shape.radius)
                if not eff.collides(self.view, pos, radius):
                    continue
                keep = eff.on_hit(self.view, p.eid, current_time)
                if not keep:
                    eff.destroy()
                    self.effects.remove(eff)
                break

    def _deflect_projectile(self, eff: Projectile, current_time: float) -> bool:
        """Return ``True`` if ``eff`` was deflected by another effect."""
        proj_pos = (
            float(eff.body.position.x),
            float(eff.body.position.y),
        )
        proj_rad = float(eff.shape.radius)
        for other in self.effects:
            if other is eff:
                continue
            owner = getattr(other, "owner", None)
            if owner == eff.owner:
                continue
            collide = getattr(other, "collides", None)
            if collide is None or not collide(self.view, proj_pos, proj_rad):
                continue
            reflector = getattr(other, "deflect_projectile", None)
            if reflector is not None:
                reflector(self.view, eff, current_time)
                return True
        return False

    def _on_projectile_removed(self, projectile: Projectile) -> None:
        """Remove ``projectile`` from the active effects list."""
        if projectile in self.effects:
            self.effects.remove(projectile)

    def _render_frame(self) -> None:
        """Render the current frame to the display surface."""
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
            self.renderer.draw_ball(pos, radius, settings.ball_color, p.color, p.dash.is_dashing)
            velocity = p.ball.body.velocity
            speed = sqrt(velocity.x * velocity.x + velocity.y * velocity.y)
            gaze = (velocity.x / speed, velocity.y / speed) if speed else p.face
            if settings.show_eyes:
                self.renderer.draw_eyes(pos, gaze, radius, p.color)
        self.renderer.draw_impacts()
        self.renderer.update_hp(
            self.players[0].ball.health / self.players[0].ball.stats.max_health,
            self.players[1].ball.health / self.players[1].ball.stats.max_health,
        )
        self.hud.draw_title(self.renderer.surface, settings.hud.title)
        self.renderer.draw_hp(self.renderer.surface, self.hud, self.labels)
        self.hud.draw_watermark(self.renderer.surface, settings.hud.watermark)
        self.renderer.present()

    def _capture_frame(self) -> None:
        """Capture the current surface for recording if headless."""
        if self.display:
            return
        frame_surface = self.renderer.surface.copy()
        frame = pygame.surfarray.array3d(frame_surface)
        self.recorder.add_frame(np.swapaxes(frame, 0, 1))

    def _play_winner_sequence(self) -> None:
        """Render the end screen animation for the winning player."""
        for p in self.players:
            weapon_audio = getattr(p.weapon, "audio", None)
            if weapon_audio is not None:
                weapon_audio.stop_idle(self.death_ts, disable=True)
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
        self.winner_weapon = self.weapon_a if self.winner == self.players[0].eid else self.weapon_b
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
                self.renderer.draw_ball(lose_pos, lose_radius, settings.ball_color, lose_p.color)
            win_radius = int(win_p.ball.shape.radius)
            self.renderer.draw_ball(win_pos, win_radius, settings.ball_color, win_p.color)
            if settings.show_eyes:
                self.renderer.draw_eyes(win_pos, win_p.face, win_radius, win_p.color)
            self.renderer.draw_impacts()
            self.renderer.draw_hp(self.renderer.surface, self.hud, self.labels)
            self.hud.draw_title(self.renderer.surface, settings.hud.title)
            self.hud.draw_watermark(self.renderer.surface, settings.hud.watermark)
            self.renderer.present()
            self._capture_frame()
        self.phase = Phase.FINISHED

    def _teardown(self, intro_elapsed: float) -> None:
        """Release resources and finalize recording."""
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
