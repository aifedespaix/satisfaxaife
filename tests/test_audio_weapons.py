import time
import time
from typing import cast

from app.audio.engine import AudioEngine
from app.audio.weapons import WeaponAudio


class StubAudioEngine:
    def __init__(self) -> None:
        self.played: list[tuple[str, object]] = []
        self.stopped: list[tuple[object, float | None]] = []
        self.stop_all_called = False

    def play_variation(
        self,
        path: str,
        volume: float | None = None,
        timestamp: float | None = None,
    ) -> object:  # noqa: D401
        handle: object = object()
        self.played.append((path, handle))
        return handle

    def get_length(self, path: str) -> float:  # noqa: D401
        return 0.0

    def stop_all(self) -> None:  # noqa: D401
        self.stop_all_called = True

    def stop_handle(self, handle: object, timestamp: float | None = None) -> None:
        self.stopped.append((handle, timestamp))


def test_melee_idle_and_touch() -> None:
    engine = StubAudioEngine()
    audio = WeaponAudio("melee", "katana", engine=cast(AudioEngine, engine), idle_gap=0.01)
    audio.start_idle(timestamp=0.0)
    time.sleep(0.05)
    audio.on_touch(timestamp=0.05)
    audio.stop_idle(timestamp=0.05)
    idle_handles = [h for p, h in engine.played if p.endswith("idle.ogg")]
    assert idle_handles
    assert any(p.endswith("touch.ogg") for p, _ in engine.played)
    assert engine.stopped[0][0] == idle_handles[-1]
    assert engine.stopped[0][1] == 0.05
    assert not engine.stop_all_called


def test_throw_events() -> None:
    engine = StubAudioEngine()
    audio = WeaponAudio("throw", "shuriken", engine=cast(AudioEngine, engine))
    audio.on_throw(timestamp=0.0)
    audio.on_touch(timestamp=0.1)
    assert any(p.endswith("throw.ogg") for p, _ in engine.played)
    assert any(p.endswith("touch.ogg") for p, _ in engine.played)
