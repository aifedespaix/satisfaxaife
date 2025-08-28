from __future__ import annotations

from typing import cast

import numpy as np

from app.audio.engine import AudioEngine
from app.core.config import settings
from app.game.match import _append_slowmo_segment


class DummyEngine:
    @staticmethod
    def _resample(array: np.ndarray, factor: float) -> np.ndarray:
        return AudioEngine._resample(array, factor)


def test_replay_audio_matches_video_and_preserves_kill_sound() -> None:
    sample_rate = AudioEngine.SAMPLE_RATE
    base_samples = sample_rate  # 1 second of match audio
    audio = np.zeros((base_samples, 1), dtype=np.int16)
    kill_amp = 10_000
    audio[-1, 0] = kill_amp

    engine = cast(AudioEngine, DummyEngine())
    final_audio = _append_slowmo_segment(audio, engine, death_ts=0.5)

    pad_samples = int(settings.end_screen.pre_slowmo_ms / 1000 * sample_rate)
    segment_len = base_samples  # death replay segment covers entire audio here
    expected = base_samples + pad_samples + int(segment_len / settings.end_screen.slowmo)
    tolerance = sample_rate // settings.fps

    assert abs(final_audio.shape[0] - expected) <= tolerance
    assert final_audio[-1, 0] == kill_amp
