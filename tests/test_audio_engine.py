import os
import time

from app.audio.engine import AudioEngine

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


def test_cache_and_cooldown() -> None:
    engine = AudioEngine()
    path = "assets/weapons/katana/touch.ogg"
    handle = engine.play_variation(path)
    assert handle is not None
    first_time = engine._last_play[path]
    assert len(engine._cache[path]) == 6
    assert engine.play_variation(path) is None
    assert engine._last_play[path] == first_time
    time.sleep(engine.COOLDOWN_MS / 1000 + 0.02)
    assert engine.play_variation(path) is not None
    engine.shutdown()


def test_capture_mixdown() -> None:
    engine = AudioEngine()
    engine.start_capture()
    path = "assets/weapons/katana/touch.ogg"
    engine.play_variation(path)
    audio = engine.end_capture()
    assert audio.ndim == 2
    assert audio.shape[0] > 0
    engine.shutdown()


def test_timestamp_offsets() -> None:
    engine = AudioEngine()
    engine.start_capture()
    path = "assets/weapons/katana/touch.ogg"
    first = 0.1
    second = 0.3
    engine.play_variation(path, timestamp=first)
    engine.play_variation(path, timestamp=second)
    assert engine._captures[0][1] == int(first * engine.SAMPLE_RATE)
    assert engine._captures[1][1] == int(second * engine.SAMPLE_RATE)
    engine.end_capture()
    engine.shutdown()

