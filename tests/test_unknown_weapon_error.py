from __future__ import annotations

import pytest

from app.core.registry import UnknownWeaponError
from app.weapons import weapon_registry


def test_unknown_weapon_error_lists_available_and_hints() -> None:
    """Unknown weapons provide a helpful, actionable error message."""
    available = weapon_registry.names()
    missing = "laser"
    with pytest.raises(UnknownWeaponError) as exc:
        weapon_registry.create(missing)
    message = str(exc.value)
    assert missing in message
    assert f"python -m app.weapons.{missing}" in message
    assert "optional dependencies" in message
    for name in available:
        assert name in message


def test_factory_unknown_weapon_error() -> None:
    """Requesting an unknown factory surfaces the same helpful message."""
    missing = "nonexistent"
    with pytest.raises(UnknownWeaponError) as exc:
        weapon_registry.factory(missing)
    message = str(exc.value)
    assert missing in message
    assert f"python -m app.weapons.{missing}" in message
    assert "optional dependencies" in message
