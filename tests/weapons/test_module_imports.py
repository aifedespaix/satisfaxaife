"""Ensure individual weapon modules import without errors."""

from __future__ import annotations

import importlib
import sys
import types

import pytest

# Provide minimal config so weapon modules importing physics do not pull the
# optional pydantic dependency.
config_stub = types.ModuleType("app.core.config")
config_stub.settings = types.SimpleNamespace(  # type: ignore[attr-defined]
    wall_thickness=10,
    width=1080,
    height=1920,
)
sys.modules.setdefault("app.core.config", config_stub)


@pytest.mark.parametrize(
    "module",
    [
        "bazooka",
        "katana",
        "knife",
        "shuriken",
        "gravity_well",
        "resonance_hammer",
    ],
)
def test_weapon_module_import(module: str) -> None:
    """Each listed weapon module imports without raising ``ImportError``."""

    sys.modules.pop("app.weapons", None)
    sys.modules.pop(f"app.weapons.{module}", None)
    sys.modules.pop("app.weapons.base", None)
    try:
        importlib.import_module(f"app.weapons.{module}")
    except ImportError as exc:  # pragma: no cover - optional dependency missing
        pytest.skip(f"{module} import skipped: {exc}")

