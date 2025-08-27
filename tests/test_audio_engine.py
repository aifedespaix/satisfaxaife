import os
import time

from app.audio.engine import AudioEngine


os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


def test_cache_and_cooldown() -> None:
    engine = AudioEngine()
    path = "assets/weapons/katana/touch.ogg"
    assert engine.play_variation(path) is True
    first_time = engine._last_play[path]
    assert len(engine._cache[path]) == 6
    assert engine.play_variation(path) is False
    assert engine._last_play[path] == first_time
    time.sleep(engine.COOLDOWN_MS / 1000 + 0.02)
    assert engine.play_variation(path) is True
    engine.shutdown()
