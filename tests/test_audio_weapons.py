import time
from typing import cast

from app.audio.engine import AudioEngine
from app.audio.weapons import WeaponAudio


class StubAudioEngine:
    def __init__(self) -> None:
        self.played: list[str] = []

    def play_variation(
        self,
        path: str,
        volume: float | None = None,
        timestamp: float | None = None,
    ) -> bool:  # noqa: D401
        self.played.append(path)
        return True

    def get_length(self, path: str) -> float:  # noqa: D401
        return 0.0

    def stop_all(self) -> None:  # noqa: D401
        pass


def test_melee_idle_and_touch() -> None:
    engine = StubAudioEngine()
    audio = WeaponAudio("melee", "katana", engine=cast(AudioEngine, engine), idle_gap=0.01)
    audio.start_idle(timestamp=0.0)
    time.sleep(0.05)
    audio.on_touch(timestamp=0.05)
    audio.stop_idle()
    assert any(path.endswith("idle.ogg") for path in engine.played)
    assert any(path.endswith("touch.ogg") for path in engine.played)


def test_throw_events() -> None:
    engine = StubAudioEngine()
    audio = WeaponAudio("throw", "shuriken", engine=cast(AudioEngine, engine))
    audio.on_throw(timestamp=0.0)
    audio.on_touch(timestamp=0.1)
    assert any(path.endswith("throw.ogg") for path in engine.played)
    assert any(path.endswith("touch.ogg") for path in engine.played)
