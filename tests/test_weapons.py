import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

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


def test_katana_blade_dimensions() -> None:
    katana = Katana()
    expected_height = DEFAULT_BALL_RADIUS * 3.0
    expected_width = DEFAULT_BALL_RADIUS / 4.0
    expected_offset = DEFAULT_BALL_RADIUS + expected_height / 2 + 1.0
    _, height = katana._sprite.get_size()
    assert height == int(expected_height)
    assert katana._blade_height == expected_height
    assert katana._blade_width == expected_width
    assert katana._blade_offset == expected_offset


def test_knife_blade_dimensions() -> None:
    knife = Knife()
    expected_height = DEFAULT_BALL_RADIUS * 2.0
    expected_width = DEFAULT_BALL_RADIUS / 4.0
    expected_offset = DEFAULT_BALL_RADIUS + expected_height / 2 + 1.0
    width, height = knife._sprite.get_size()
    assert height == int(expected_height)
    assert width > 0
    assert knife._blade_height == expected_height
    assert knife._blade_width == expected_width
    assert knife._blade_offset == expected_offset


def test_bazooka_missile_radius() -> None:
    bazooka = Bazooka()
    assert bazooka.missile_radius == DEFAULT_BALL_RADIUS


def test_weapon_range_types() -> None:
    assert Bazooka.range_type == "distant"
    assert Shuriken.range_type == "distant"
    assert Katana.range_type == "contact"
    assert Knife.range_type == "contact"
