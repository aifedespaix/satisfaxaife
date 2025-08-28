from __future__ import annotations

import numpy as np

from typing import cast

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
    final_audio = _append_slowmo_segment(audio, engine)

    base_frames = int(base_samples / sample_rate * settings.fps)
    buffer_len = int(settings.end_screen.slowmo_duration * settings.fps)
    repeat = max(1, int(1 / settings.end_screen.slowmo))
    freeze_frames = int(settings.end_screen.freeze_ms / 1000 * settings.fps)
    fade_frames = int(settings.end_screen.fade_ms / 1000 * settings.fps)
    expected_frames = base_frames + buffer_len * repeat + freeze_frames + fade_frames
    expected_samples = int(expected_frames / settings.fps * sample_rate)
    tolerance = sample_rate // settings.fps

    assert abs(final_audio.shape[0] - expected_samples) <= tolerance
    assert final_audio[-1, 0] == kill_amp
