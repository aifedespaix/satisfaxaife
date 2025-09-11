from __future__ import annotations

from app.render.renderer import Renderer


def test_trails_are_isolated_per_state_key() -> None:
    renderer = Renderer(100, 100)
    team_color = (255, 0, 0)

    key1 = object()
    key2 = object()

    # Draw two frames for entity 1 to accumulate a trail point.
    renderer.draw_ball((10.0, 10.0), 10, (255, 255, 255), team_color, state_key=key1)
    renderer.draw_ball((20.0, 10.0), 10, (255, 255, 255), team_color, state_key=key1)
    state1 = renderer._get_state(key1)
    len1 = len(state1.trail)
    assert len1 >= 1

    # Draw two frames for entity 2; ensure it does not affect entity 1 trail.
    renderer.draw_ball((10.0, 20.0), 10, (255, 255, 255), team_color, state_key=key2)
    renderer.draw_ball((20.0, 20.0), 10, (255, 255, 255), team_color, state_key=key2)
    state2 = renderer._get_state(key2)
    assert len(state2.trail) >= 1

    # Re-check entity 1 trail is unchanged by entity 2 draws.
    assert len(renderer._get_state(key1).trail) == len1

