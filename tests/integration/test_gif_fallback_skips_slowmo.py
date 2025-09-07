from __future__ import annotations

from pathlib import Path

import pytest

import imageio
from app.core.config import settings
from app.game.match import run_match
from app.render.renderer import Renderer
from app.video.recorder import Recorder
from app.weapons import weapon_registry
from tests.integration.helpers import InstantKillWeapon


def test_gif_fallback_skips_slowmo(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Slow-motion is skipped when the recorder outputs a GIF."""
    if "instakill" not in weapon_registry.names():
        weapon_registry.register("instakill", InstantKillWeapon)

    original_get_writer = imageio.get_writer

    def fail_mp4(*args: object, **kwargs: object) -> object:
        if kwargs.get("codec") == "libx264":
            raise OSError("mp4 writer unavailable")
        return original_get_writer(*args, **kwargs)

    monkeypatch.setattr(imageio, "get_writer", fail_mp4)

    called = False

    def fake_append(*_args: object, **_kwargs: object) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr("app.game.controller.append_slowmo_ending", fake_append)

    out = tmp_path / "out.mp4"
    recorder = Recorder(settings.width, settings.height, settings.fps, out)
    assert recorder.path is not None and recorder.path.suffix == ".gif"

    renderer = Renderer(settings.width, settings.height)
    run_match("instakill", "instakill", recorder, renderer, max_seconds=1)

    assert recorder.path.exists()
    assert not called
