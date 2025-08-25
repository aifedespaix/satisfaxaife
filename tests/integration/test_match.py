from __future__ import annotations

import os
from pathlib import Path

from app.core.config import settings
from app.core.types import EntityId
from app.game.match import run_match
from app.video.recorder import Recorder


def test_match_generates_video_and_winner() -> None:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    out = Path("out") / "integration_match.mp4"
    out.parent.mkdir(exist_ok=True)
    recorder = Recorder(settings.width, settings.height, settings.fps, out)
    winner = run_match(2, "katana", "shuriken", recorder)
    assert out.exists()
    assert winner is None or isinstance(winner, EntityId)
