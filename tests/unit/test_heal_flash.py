from app.core.config import settings
from app.render.renderer import Renderer


def test_heal_flash_colors_surface() -> None:
    renderer = Renderer(width=100, height=100, display=False)
    team_color = (10, 20, 30)
    pos = (50.0, 50.0)
    radius = 10
    key = object()

    renderer.trigger_heal_flash_for(key, duration=0.1)
    renderer.clear()
    renderer.draw_ball(pos, radius, settings.ball_color, team_color, state_key=key)
    color = renderer.surface.get_at((50, 50))
    assert color.g > 180 and color.r < 120 and color.b < 120

    # Let the flash fade out
    for _ in range(int(0.2 / settings.dt)):
        renderer.clear()
        renderer.draw_ball(pos, radius, settings.ball_color, team_color, state_key=key)

    renderer.clear()
    renderer.draw_ball(pos, radius, settings.ball_color, team_color, state_key=key)
    color_after = renderer.surface.get_at((50, 50))
    assert (
        abs(color_after.r - settings.ball_color[0]) < 8
        and abs(color_after.g - settings.ball_color[1]) < 8
        and abs(color_after.b - settings.ball_color[2]) < 8
    )

