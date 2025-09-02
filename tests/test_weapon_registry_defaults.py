"""Tests for default weapon registry entries."""

from __future__ import annotations

import importlib
import sys
import types

# Provide a minimal configuration module so that weapon modules importing the
# physics engine do not require the optional pydantic dependency.
config_stub = types.ModuleType("app.core.config")
config_stub.settings = types.SimpleNamespace(  # type: ignore[attr-defined]
    wall_thickness=10,
    width=1080,
    height=1920,
)
sys.modules.setdefault("app.core.config", config_stub)


def test_weapon_registry_registers_default_weapons() -> None:
    """Default weapons are registered on package import."""
    for mod in [
        "app.weapons",
        "app.weapons.base",
        "app.weapons.bazooka",
        "app.weapons.katana",
        "app.weapons.knife",
        "app.weapons.shuriken",
    ]:
        sys.modules.pop(mod, None)

    weapons = importlib.import_module("app.weapons")
    names = weapons.weapon_registry.names()

    expected = {"bazooka", "katana", "knife", "shuriken"}
    assert expected <= set(names)
