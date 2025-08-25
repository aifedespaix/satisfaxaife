from __future__ import annotations

from math import sqrt

from app.core.config import settings
from app.render.hud import Hud
from app.render.renderer import Renderer
from app.video.recorder import Recorder
from app.world.entities import Ball
from app.world.physics import PhysicsWorld
from app.world.projectiles import Projectile


def run_match(seconds: int, recorder: Recorder) -> None:
    """Run a minimal game loop and record frames."""
    world = PhysicsWorld()
    renderer = Renderer(settings.width, settings.height)
    hud = Hud()

    ball_a = Ball.spawn(world, (settings.width * 0.25, settings.height * 0.5))
    ball_b = Ball.spawn(world, (settings.width * 0.75, settings.height * 0.5))
    ball_a.body.velocity = (200.0, 150.0)
    ball_b.body.velocity = (-200.0, 150.0)
    entities: list[Ball] = [ball_a, ball_b]
    projectiles: list[Projectile] = []

    total_frames = int(seconds * settings.fps)
    for _ in range(total_frames):
        for entity in entities:
            entity.cap_speed()
        for projectile in projectiles:
            projectile.step(settings.dt)
        world.step(settings.dt)

        renderer.clear()
        for projectile in projectiles:
            proj_pos = (
                float(projectile.body.position.x),
                float(projectile.body.position.y),
            )
            renderer.draw_projectile(proj_pos, int(projectile.shape.radius), (255, 255, 0))
        for idx, entity in enumerate(entities):
            pos = (float(entity.body.position.x), float(entity.body.position.y))
            radius = int(entity.shape.radius)
            base_color = settings.ball_color
            team_color = (255, 0, 0) if idx == 0 else (0, 0, 255)
            renderer.draw_ball(pos, radius, base_color, team_color)
            vx, vy = entity.body.velocity
            speed = sqrt(vx * vx + vy * vy)
            gaze = (vx / speed, vy / speed) if speed else (0.0, 0.0)
            renderer.draw_eyes(pos, gaze, radius, team_color)

        hud.draw_title(renderer.surface, "Qui gagne : Katana ou Shuriken ?")
        hud.draw_hp_bars(
            renderer.surface,
            ball_a.health / ball_a.stats.max_health,
            ball_b.health / ball_b.stats.max_health,
            ("Katana", "Shuriken"),
        )
        hud.draw_watermark(renderer.surface)

        renderer.present()
        frame = renderer.capture_frame()
        recorder.add_frame(frame)

    recorder.close()
