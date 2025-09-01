import pymunk


def test_apply_impulse_at_local_point_updates_velocity() -> None:
    body = pymunk.Body(1.0, 1.0)
    body.velocity = (1.0, 2.0)
    body.apply_impulse_at_local_point((3.0, -4.0))
    assert body.velocity.x == 4.0
    assert body.velocity.y == -2.0
