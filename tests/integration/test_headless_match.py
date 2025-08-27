from __future__ import annotations

import subprocess
from pathlib import Path

import imageio_ffmpeg
import pytest

from app.core.config import settings
from app.game.match import MatchTimeout, run_match
from app.render.renderer import Renderer
from app.video.recorder import Recorder


def test_headless_match_records_video() -> None:
    artifacts = Path("artifacts")
    artifacts.mkdir(exist_ok=True)
    out = artifacts / "mini_seed1_katana_vs_shuriken.mp4"
    recorder = Recorder(settings.width, settings.height, settings.fps, out)
    renderer = Renderer(settings.width, settings.height)
    with pytest.raises(MatchTimeout):
        run_match("katana", "shuriken", recorder, renderer, max_seconds=2)
    assert out.exists() and out.stat().st_size > 0
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    info = subprocess.run([ffmpeg, "-i", str(out)], capture_output=True, text=True)
    assert "Audio:" in info.stderr
