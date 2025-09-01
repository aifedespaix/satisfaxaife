import pymunk


def test_circle_bounces_off_vertical_segment() -> None:
    space = pymunk.Space()
    body = pymunk.Body(1.0, pymunk.moment_for_circle(1.0, 0.0, 5.0))
    body.position = (5.0, 5.0)
    body.velocity = (-10.0, 0.0)
    circle = pymunk.Circle(body, 5.0)
    circle.elasticity = 1.0
    segment = pymunk.Segment(space.static_body, (0.0, -10.0), (0.0, 10.0), 1.0)
    segment.elasticity = 1.0
    space.add(body, circle, segment)
    space.step(1.0)
    assert body.position.x == 5.0
    assert body.velocity.x == 10.0


def test_circle_bounces_off_horizontal_segment() -> None:
    space = pymunk.Space()
    body = pymunk.Body(1.0, pymunk.moment_for_circle(1.0, 0.0, 5.0))
    body.position = (5.0, 5.0)
    body.velocity = (0.0, -10.0)
    circle = pymunk.Circle(body, 5.0)
    circle.elasticity = 1.0
    segment = pymunk.Segment(space.static_body, (-10.0, 0.0), (10.0, 0.0), 1.0)
    segment.elasticity = 1.0
    space.add(body, circle, segment)
    space.step(1.0)
    assert body.position.y == 5.0
    assert body.velocity.y == 10.0
