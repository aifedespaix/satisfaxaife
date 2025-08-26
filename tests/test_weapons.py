from app.weapons.katana import Katana
from app.weapons.shuriken import Shuriken
from app.world.entities import DEFAULT_BALL_RADIUS


def test_shuriken_sprite_and_radius() -> None:
    shuriken = Shuriken()
    expected_size = int(DEFAULT_BALL_RADIUS * 2 / 3)
    width, height = shuriken._sprite.get_size()
    assert max(width, height) == expected_size
    assert shuriken._radius == DEFAULT_BALL_RADIUS / 3


def test_katana_sprite_height() -> None:
    katana = Katana()
    expected_height = int(DEFAULT_BALL_RADIUS * 3)
    _, height = katana._sprite.get_size()
    assert height == expected_height
