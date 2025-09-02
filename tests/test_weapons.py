from app.weapons.bazooka import Bazooka
from app.weapons.katana import Katana
from app.weapons.knife import Knife
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


def test_knife_sprite_loaded() -> None:
    knife = Knife()
    width, height = knife._sprite.get_size()
    assert width > 0 and height > 0


def test_bazooka_missile_radius() -> None:
    bazooka = Bazooka()
    assert bazooka.missile_radius == DEFAULT_BALL_RADIUS


def test_weapon_range_types() -> None:
    assert Bazooka.range_type == "distant"
    assert Shuriken.range_type == "distant"
    assert Katana.range_type == "contact"
    assert Knife.range_type == "contact"
