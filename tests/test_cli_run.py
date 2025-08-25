from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from app.cli import app


def test_run_creates_video(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "test.mp4"
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
    video_path = out if out.exists() else out.with_suffix(".gif")
    assert video_path.exists()


def test_run_display_mode_no_file(tmp_path: Path) -> None:
    runner = CliRunner()
    out = tmp_path / "test.mp4"
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
            "--display",
        ],
    )
    assert result.exit_code == 0
    assert not out.exists()
    assert not out.with_suffix(".gif").exists()
