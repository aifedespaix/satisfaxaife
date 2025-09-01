from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytest.importorskip("typer")
pytest.importorskip("pydantic")
from pytest import MonkeyPatch
from typer.testing import CliRunner

import app.audio.weapons as weapons
import app.cli as cli_module
from app.audio import reset_default_engine
from app.audio.engine import AudioEngine
from app.cli import app
from app.core.config import settings
from app.intro.config import IntroConfig
from app.render.intro_renderer import IntroRenderer
from app.render.renderer import Renderer
from app.video.recorder import NullRecorder

imageio_ffmpeg = pytest.importorskip("imageio_ffmpeg")


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

    # On force un timeout en remplaçant GameController.run
    from app.game.controller import GameController
    from app.game.match import MatchTimeout

    def run_short(self: GameController) -> str | None:  # noqa: ARG001
        raise MatchTimeout("Match exceeded 0 seconds")

    monkeypatch.setattr(GameController, "run", run_short)

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
    captured_recorder: dict[str, NullRecorder] = {}

    class InspectableNullRecorder(NullRecorder):
        def __init__(self) -> None:
            super().__init__()
            captured_recorder["instance"] = self

    monkeypatch.setattr(cli_module, "NullRecorder", InspectableNullRecorder)

    runner = CliRunner()
    with runner.isolated_filesystem():
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
        assert captured["width"] == settings.width
        assert captured["height"] == settings.height
        assert captured["display"] is True
        assert captured_recorder["instance"].path is None
        # En mode display, aucun fichier ne doit être créé
        assert not Path("generated").exists()


def test_run_uses_dummy_audio_driver(monkeypatch: MonkeyPatch) -> None:
    generated = Path("generated")
    if generated.exists():
        shutil.rmtree(generated)
    reset_default_engine()
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
    assert weapons._DEFAULT_ENGINE is None
    if generated.exists():
        shutil.rmtree(generated)


def test_intro_weapons_option(monkeypatch: MonkeyPatch, tmp_path: Path) -> None:
    captured: dict[str, IntroConfig | None] = {}

    original_init = IntroRenderer.__init__

    def spy_init(
        self: IntroRenderer, width: int, height: int, config: IntroConfig | None = None
    ) -> None:
        captured["config"] = config
        original_init(self, width, height, config=config)

    monkeypatch.setattr(IntroRenderer, "__init__", spy_init)
    monkeypatch.setattr(cli_module, "Recorder", NullRecorder)

    runner = CliRunner()
    left = tmp_path / "a.png"
    right = tmp_path / "b.png"
    with runner.isolated_filesystem():
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
                "--intro-weapons",
                f"left={left}",
                f"right={right}",
            ],
        )

    assert result.exit_code == 0
    config = captured["config"]
    assert config is not None
    assert config.weapon_a_path == left
    assert config.weapon_b_path == right
    assert config.logo_in == 0.0
    assert config.weapons_in == 0.0
    assert config.hold == 1.0
    assert config.fade_out == 0.25
