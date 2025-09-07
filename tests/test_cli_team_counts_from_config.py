from __future__ import annotations

from pathlib import Path
from typing import Any

from typer.testing import CliRunner

import app.cli as cli_module
from app.cli import app
from app.core.config import settings
from app.video.recorder import NullRecorder


def test_run_applies_team_counts_from_config(monkeypatch: Any) -> None:
    """CLI overrides team sizes using values from ``config.yml``."""
    captured: dict[str, int] = {}

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
        captured["team_a_count"] = settings.team_a_count
        captured["team_b_count"] = settings.team_b_count

        class _C:
            def run(self) -> str:
                return weapon_a

        return _C()

    from app.game import match as match_module

    monkeypatch.setattr(match_module, "create_controller", fake_create_controller)
    monkeypatch.setattr(settings, "team_a_count", 1)
    monkeypatch.setattr(settings, "team_b_count", 1)

    runner = CliRunner()
    with runner.isolated_filesystem():
        Path("config.yml").write_text(
            "\n".join([
                "team_a_count: 2",
                "team_b_count: 2",
            ]),
            encoding="utf-8",
        )
        result = runner.invoke(app, ["run"])

    assert result.exit_code == 0
    assert captured["team_a_count"] == 2
    assert captured["team_b_count"] == 2
