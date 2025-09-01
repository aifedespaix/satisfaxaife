import sys
import types
from typing import Any, cast

pygame_stub = cast(Any, types.ModuleType("pygame"))
pygame_stub.mixer = types.ModuleType("mixer")
pygame_stub.sndarray = types.ModuleType("sndarray")
sys.modules.setdefault("pygame", pygame_stub)
sys.modules.setdefault("pygame.sndarray", pygame_stub.sndarray)
sys.modules.setdefault("pygame.mixer", pygame_stub.mixer)

np_stub = types.ModuleType("numpy")
sys.modules.setdefault("numpy", np_stub)

from app.audio import BallAudio  # noqa: E402
from app.audio.engine import AudioEngine  # noqa: E402


class StubAudioEngine:
    def __init__(self) -> None:
        self.played: list[str] = []
        self.timestamps: list[float | None] = []

    def play_variation(
        self,
        path: str,
        volume: float | None = None,
        timestamp: float | None = None,
        *,
        cooldown_ms: int | None = None,
    ) -> object:  # noqa: D401
        self.played.append(path)
        self.timestamps.append(timestamp)
        return object()


def test_ball_explosion_event() -> None:
    engine = StubAudioEngine()
    audio = BallAudio(engine=cast(AudioEngine, engine))
    audio.on_explode(timestamp=0.5)
    assert any(path.endswith("explose.ogg") for path in engine.played)
    assert engine.timestamps[0] == 0.5


def test_ball_hit_event(monkeypatch: Any) -> None:
    engine = StubAudioEngine()
    audio = BallAudio(engine=cast(AudioEngine, engine))

    def fake_choice(options: list[str]) -> str:
        assert len(options) == 3
        return options[1]

    monkeypatch.setattr("app.audio.balls.random.choice", fake_choice)
    audio.on_hit(timestamp=1.25)
    assert engine.played[0].endswith("hit-b.ogg")
    assert engine.timestamps[0] == 1.25
