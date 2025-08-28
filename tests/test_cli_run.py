from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import imageio_ffmpeg
from pytest import MonkeyPatch
from typer.testing import CliRunner

from app.audio.engine import AudioEngine
from app.cli import app
from app.core.config import settings
from app.render.renderer import Renderer
from app.video.recorder import Recorder


def test_run_creates_video(tmp_path: Path) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "run",
            "--seed",
            "1",
            "--weapon-a",
            "katana",
            "--weapon-b",
            "shuriken",
        ],
    )
    assert result.exit_code == 0
    generated_dir = Path("generated")
    files = list(generated_dir.glob("*.mp4")) or list(generated_dir.glob("*.gif"))
    assert len(files) == 1
    video_path = files[0]
    assert video_path.exists()
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    info = subprocess.run([ffmpeg, "-i", str(video_path)], capture_output=True, text=True)
    assert "Audio:" in info.stderr


def test_run_timeout(monkeypatch: MonkeyPatch) -> None:
    runner = CliRunner()

    # On force un timeout en remplaçant app.cli.run_match par un wrapper
    from app.game import match as match_module

    def run_match_short(
        weapon_a: str,
        weapon_b: str,
        recorder: Recorder,
        renderer: Renderer | None = None,
    ) -> None:
        # max_seconds=0 provoque systématiquement un MatchTimeout
        match_module.run_match(weapon_a, weapon_b, recorder, renderer, max_seconds=0)

    monkeypatch.setattr("app.cli.run_match", run_match_short)

    result = runner.invoke(
        app,
        [
            "run",
            "--seed",
            "1",
            "--weapon-a",
            "katana",
            "--weapon-b",
            "shuriken",
        ],
    )
    assert result.exit_code != 0
    assert "exceeded" in (result.stderr or "").lower()
    generated_dir = Path("generated")
    assert generated_dir.exists()
    assert list(generated_dir.glob("*")) == []


def test_run_display_mode_no_file(monkeypatch: MonkeyPatch) -> None:
    captured: dict[str, int | bool] = {}

    original_init = Renderer.__init__

    def spy_init(
        self: Renderer,
        width: int = settings.width,
        height: int = settings.height,
        display: bool = False,
    ) -> None:
        captured["width"] = width
        captured["height"] = height
        captured["display"] = display
        original_init(self, width, height, display=display)

    monkeypatch.setattr(Renderer, "__init__", spy_init)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "run",
            "--seed",
            "1",
            "--weapon-a",
            "katana",
            "--weapon-b",
            "shuriken",
            "--display",
        ],
    )

    assert result.exit_code == 0
    assert captured["width"] == settings.width // 2
    assert captured["height"] == settings.height // 2
    assert captured["display"] is True
    # En mode display, aucun fichier ne doit être créé
    assert not Path("generated").exists()


def test_run_uses_dummy_audio_driver(monkeypatch: MonkeyPatch) -> None:
    generated = Path("generated")
    if generated.exists():
        shutil.rmtree(generated)
    monkeypatch.setenv("SDL_AUDIODRIVER", "original")

    recorded: dict[str, str | None] = {}
    original_init = AudioEngine.__init__

    def spy_init(self: AudioEngine) -> None:
        recorded["driver"] = os.environ.get("SDL_AUDIODRIVER")
        original_init(self)

    monkeypatch.setattr(AudioEngine, "__init__", spy_init)

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "run",
            "--seed",
            "1",
            "--weapon-a",
            "katana",
            "--weapon-b",
            "shuriken",
        ],
    )
    assert result.exit_code == 0
    assert recorded["driver"] == "dummy"
    assert os.environ["SDL_AUDIODRIVER"] == "original"
    if generated.exists():
        shutil.rmtree(generated)
