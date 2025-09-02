"""Tests that failed weapon imports surface warnings."""

from __future__ import annotations

import importlib
import logging
import sys
import types

import pytest


def _clear_weapon_modules() -> None:
    """Remove weapon modules from :data:`sys.modules` for a clean import."""
    for name in list(sys.modules):
        if name.startswith("app.weapons"):
            sys.modules.pop(name)


def test_failed_import_logs_warning(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Import failures should emit a warning with module and error details."""

    # Provide minimal configuration to satisfy optional dependencies.
    config_stub = types.ModuleType("app.core.config")
    config_stub.settings = types.SimpleNamespace(  # type: ignore[attr-defined]
        wall_thickness=10,
        width=1080,
        height=1920,
    )
    sys.modules.setdefault("app.core.config", config_stub)

    _clear_weapon_modules()

    real_import_module = importlib.import_module

    def failing_import(name: str, package: str | None = None) -> types.ModuleType:
        if name == "app.weapons.katana":
            raise RuntimeError("boom")
        return real_import_module(name, package)

    monkeypatch.setattr(importlib, "import_module", failing_import)

    with caplog.at_level(logging.WARNING):
        importlib.import_module("app.weapons")

    messages = [record.getMessage() for record in caplog.records]
    assert any("Failed to import optional weapon module 'katana': boom" in msg for msg in messages)
