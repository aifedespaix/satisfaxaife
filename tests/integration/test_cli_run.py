from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from app.cli import app


def test_run_creates_video() -> None:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    runner = CliRunner()
    out = Path("out") / "cli_run.mp4"
    out.parent.mkdir(exist_ok=True)
    result = runner.invoke(
        app,
        [
            "run",
            "--seconds",
            "1",
            "--seed",
            "1",
            "--weapon-a",
            "katana",
            "--weapon-b",
            "shuriken",
            "--out",
            str(out),
        ],
    )
    assert result.exit_code == 0
    assert out.exists()
