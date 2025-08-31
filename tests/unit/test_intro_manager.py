from __future__ import annotations

from typing import Any, cast

import pytest

pygame = pytest.importorskip("pygame")

from app.intro import IntroConfig, IntroManager, IntroState  # noqa: E402


class StubEngine:
    def __init__(self) -> None:
        self.played: list[tuple[str, float | None]] = []

    def play_variation(
        self, path: str, volume: float | None = None, timestamp: float | None = None
    ) -> None:
        self.played.append((path, timestamp))


def test_intro_manager_start_state() -> None:
    manager = IntroManager(engine=cast(Any, StubEngine()))
    manager.start()
    assert manager.state == IntroState.LOGO_IN


def test_intro_manager_transitions() -> None:
    config = IntroConfig(logo_in=0.1, weapons_in=0.1, hold=0.1, fade_out=0.1, allow_skip=False)
    stub = StubEngine()
    manager = IntroManager(config=config, engine=cast(Any, stub))
    manager.start()
    for expected in (
        IntroState.WEAPONS_IN,
        IntroState.HOLD,
        IntroState.FADE_OUT,
        IntroState.DONE,
    ):
        manager.update(0.1)
        assert manager.state == expected
    assert manager.is_finished()


def test_intro_manager_skip() -> None:
    config = IntroConfig(
        logo_in=10.0,
        weapons_in=10.0,
        hold=10.0,
        fade_out=10.0,
        allow_skip=True,
        skip_key=pygame.K_s,
    )
    manager = IntroManager(config=config, engine=cast(Any, StubEngine()))
    manager.start()

    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_s})
    manager.update(0.0, [event])

    assert manager.state == IntroState.DONE
    assert manager.is_finished()


def test_intro_manager_skip_disallowed() -> None:
    config = IntroConfig(
        logo_in=10.0,
        weapons_in=10.0,
        hold=10.0,
        fade_out=10.0,
        allow_skip=False,
        skip_key=pygame.K_s,
    )
    manager = IntroManager(config=config, engine=cast(Any, StubEngine()))
    manager.start()

    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_s})
    manager.update(0.0, [event])

    assert manager.state == IntroState.LOGO_IN


def test_intro_manager_fight_sound() -> None:
    config = IntroConfig(logo_in=0.1, weapons_in=0.1, hold=0.1, fade_out=0.1, allow_skip=False)
    stub = StubEngine()
    manager = IntroManager(config=config, engine=cast(Any, stub))
    manager.start()
    for _ in range(3):
        manager.update(0.1)
    assert len(stub.played) == 1
    path, timestamp = stub.played[0]
    assert path.endswith("fight.ogg")
    expected = config.logo_in + config.weapons_in + config.hold
    assert timestamp == pytest.approx(expected)
