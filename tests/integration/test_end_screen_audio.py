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
def test_end_screen_audio_contains_explosion_and_slow_segment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Audio replay should be longer and contain the kill sound."""

    if "instakill" not in weapon_registry.names():
        weapon_registry.register("instakill", InstantKillWeapon)

    recorder = SpyRecorder()

    captured: dict[str, np.ndarray] = {}
    original = _append_slowmo_segment

    def capture(audio: np.ndarray, engine: AudioEngine, death_ts: float) -> np.ndarray:
        captured["real"] = audio.copy()
        return original(audio, engine, death_ts)

    monkeypatch.setattr("app.game.match._append_slowmo_segment", capture)

    with temporary_sdl_audio_driver("dummy"):
        renderer = Renderer(settings.width, settings.height)
        run_match("instakill", "instakill", recorder, renderer, max_seconds=1)

    raw = captured["real"]
    final = recorder.audio
    assert final is not None

    pad_samples = int(settings.end_screen.pre_slowmo_ms / 1000 * AudioEngine.SAMPLE_RATE)
    segment_samples = int(
        (settings.end_screen.slowmo_duration + settings.end_screen.explosion_duration)
        * AudioEngine.SAMPLE_RATE
    )
    expected_min = raw.shape[0] + pad_samples + int(segment_samples / settings.end_screen.slowmo)
    assert final.shape[0] >= expected_min

    slow_start = raw.shape[0] + pad_samples
    assert np.any(final[slow_start:] != 0)

    reset_default_engine()
