from __future__ import annotations

import numpy as np
import pytest

from app.audio import AudioEngine, reset_default_engine
from app.audio.env import temporary_sdl_audio_driver
from app.core.config import settings
from app.game.match import _append_slowmo_segment, run_match
from app.render.renderer import Renderer
from app.weapons import weapon_registry
from tests.integration.helpers import InstantKillWeapon, SpyRecorder


@pytest.mark.integration
@pytest.mark.usefixtures("monkeypatch")
def test_slowmo_segment_has_expected_length_and_content(monkeypatch: pytest.MonkeyPatch) -> None:
    if "instakill" not in weapon_registry.names():
        weapon_registry.register("instakill", InstantKillWeapon)

    recorder = SpyRecorder()
    renderer = Renderer(settings.width, settings.height)

    captured: dict[str, np.ndarray] = {}
    original = _append_slowmo_segment

    def capture(audio: np.ndarray, engine: AudioEngine, death_ts: float) -> np.ndarray:
        captured["raw"] = audio.copy()
        return original(audio, engine, death_ts)

    monkeypatch.setattr("app.game.match._append_slowmo_segment", capture)

    with temporary_sdl_audio_driver("dummy"):
        run_match("instakill", "instakill", recorder, renderer, max_seconds=1)

    raw = captured["raw"]
    final = recorder.audio
    assert final is not None

    pad_samples = int(settings.end_screen.pre_slowmo_ms / 1000 * AudioEngine.SAMPLE_RATE)
    slow_start = raw.shape[0] + pad_samples
    slow_samples = int(
        settings.end_screen.slowmo_duration / settings.end_screen.slowmo * AudioEngine.SAMPLE_RATE
    )
    assert final.shape[0] >= slow_start + slow_samples
    slow_segment = final[slow_start : slow_start + slow_samples]
    assert slow_segment.shape[0] == slow_samples
    assert np.any(slow_segment != 0)

    reset_default_engine()
