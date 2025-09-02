from dataclasses import FrozenInstanceError

import pytest

from app.core.types import Damage


def test_damage_is_immutable() -> None:
    damage = Damage(5.0)
    with pytest.raises(FrozenInstanceError):
        damage.amount = 10.0  # type: ignore[misc]


def test_damage_value_preserved() -> None:
    damage = Damage(12.5)
    assert damage.amount == 12.5
