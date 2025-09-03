from __future__ import annotations

from pathlib import Path
from typing import Any

from typer.testing import CliRunner

import app.cli as cli_module
from app.cli import app
from app.video.recorder import NullRecorder


def test_run_reads_config_yaml(monkeypatch: Any) -> None:
    """When no params are given, CLI uses values from config.yml."""
    captured: dict[str, object] = {}

    # Avoid invoking ffmpeg by using a null recorder
    monkeypatch.setattr(cli_module, "Recorder", NullRecorder)

    def fake_renderer(
        width: int,
        height: int,
        display: bool = False,
        *,
        debug: bool = False,
    ) -> Any:
        captured["debug"] = debug
        return object()

    monkeypatch.setattr(cli_module, "Renderer", fake_renderer)

    # Spy on controller creation to capture arguments
    def fake_create_controller(
        weapon_a: str,
        weapon_b: str,
        recorder: Any,
        renderer: Any,
        *,
        max_seconds: int = 120,
        ai_transition_seconds: int = 20,
        display: bool = False,
        intro_config: Any = None,
        rng: Any = None,
    ) -> Any:
        captured["weapon_a"] = weapon_a
        captured["weapon_b"] = weapon_b
        captured["max_seconds"] = max_seconds
        captured["ai_transition_seconds"] = ai_transition_seconds

        class _C:
            def run(self) -> str:
                return weapon_a  # arbitrary winner

        return _C()

    from app.game import match as match_module

    monkeypatch.setattr(match_module, "create_controller", fake_create_controller)

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("config.yml").write_text(
            "\n".join(
                [
                    "weapon_a: knife",
                    "weapon_b: shuriken",
                    "max_simulation_seconds: 42",
                    "ai_transition_seconds: 30",
                    "seed: 1234",
                    "debug: true",
                ]
            ),
            encoding="utf-8",
        )
        result = runner.invoke(app, ["run"])  # no parameters
    assert result.exit_code == 0

    assert captured["weapon_a"] == "knife"
    assert captured["weapon_b"] == "shuriken"
    assert captured["max_seconds"] == 42
    assert captured["ai_transition_seconds"] == 30
    assert captured["debug"] is True


def test_run_uses_default_ai_transition_seconds(monkeypatch: Any) -> None:
    """CLI falls back to default ``ai_transition_seconds`` when absent."""
    captured: dict[str, object] = {}

    monkeypatch.setattr(cli_module, "Recorder", NullRecorder)

    def fake_renderer(
        width: int,
        height: int,
        display: bool = False,
        *,
        debug: bool = False,
    ) -> Any:
        return object()

    monkeypatch.setattr(cli_module, "Renderer", fake_renderer)

    def fake_create_controller(
        weapon_a: str,
        weapon_b: str,
        recorder: Any,
        renderer: Any,
        *,
        max_seconds: int = 120,
        ai_transition_seconds: int = 20,
        display: bool = False,
        intro_config: Any = None,
        rng: Any = None,
    ) -> Any:
        captured["ai_transition_seconds"] = ai_transition_seconds

        class _C:
            def run(self) -> str:
                return weapon_a

        return _C()

    from app.game import match as match_module

    monkeypatch.setattr(match_module, "create_controller", fake_create_controller)

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("config.yml").write_text(
            "\n".join(
                [
                    "weapon_a: knife",
                    "weapon_b: shuriken",
                    "seed: 1234",
                ]
            ),
            encoding="utf-8",
        )
        result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    assert captured["ai_transition_seconds"] == 20
