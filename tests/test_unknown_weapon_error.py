from __future__ import annotations

import pytest

from app.core.registry import UnknownWeaponError
from app.weapons import weapon_registry


def test_unknown_weapon_error_lists_available() -> None:
    """Unknown weapons provide a helpful error message."""
    available = weapon_registry.names()
    missing = "laser"
    with pytest.raises(UnknownWeaponError) as exc:
        weapon_registry.create(missing)
    message = str(exc.value)
    assert missing in message
    for name in available:
        assert name in message
