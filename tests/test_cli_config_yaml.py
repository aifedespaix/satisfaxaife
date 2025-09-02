from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

import app.cli as cli_module
from app.cli import app


def test_run_reads_config_yaml(monkeypatch) -> None:
    """When no params are given, CLI uses values from config.yml."""
    captured: dict[str, object] = {}

    # Avoid invoking ffmpeg by using a null recorder
    monkeypatch.setattr(cli_module, "Recorder", cli_module.NullRecorder)

    # Spy on controller creation to capture arguments
    def fake_create_controller(
        weapon_a: str,
        weapon_b: str,
        recorder,
        renderer,
        *,
        max_seconds: int = 120,
        display: bool = False,
        intro_config=None,
        rng=None,
    ):
        captured["weapon_a"] = weapon_a
        captured["weapon_b"] = weapon_b
        captured["max_seconds"] = max_seconds

        class _C:
            def run(self):
                return weapon_a  # arbitrary winner

        return _C()

    from app.game import match as match_module
    monkeypatch.setattr(match_module, "create_controller", fake_create_controller)

    runner = CliRunner()
    result = runner.invoke(app, ["run"])  # no parameters
    assert result.exit_code == 0

    # Values in the repository's config.yml
    assert captured["weapon_a"] == "katana"
    assert captured["weapon_b"] == "shuriken"
    assert captured["max_seconds"] == 120
