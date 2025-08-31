from app.core.config import settings
from app.render.renderer import Renderer


def test_hit_flash_colors_surface() -> None:
    renderer = Renderer(width=100, height=100, display=False)
    team_color = (1, 2, 3)
    pos = (50.0, 50.0)
    radius = 10
    renderer.trigger_hit_flash(team_color, duration=0.1)
    renderer.clear()
    renderer.draw_ball(pos, radius, settings.ball_color, team_color)
    color = renderer.surface.get_at((50, 50))
    assert color.r > 200 and color.g < 100 and color.b < 100

    for _ in range(int(0.2 / settings.dt)):
        renderer.clear()
        renderer.draw_ball(pos, radius, settings.ball_color, team_color)
    renderer.clear()
    renderer.draw_ball(pos, radius, settings.ball_color, team_color)
    color_after = renderer.surface.get_at((50, 50))
    assert (
        abs(color_after.r - settings.ball_color[0]) < 5
        and abs(color_after.g - settings.ball_color[1]) < 5
        and abs(color_after.b - settings.ball_color[2]) < 5
    )
