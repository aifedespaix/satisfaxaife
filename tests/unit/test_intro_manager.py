from __future__ import annotations

import pytest

pygame = pytest.importorskip("pygame")

from app.intro import IntroConfig, IntroManager, IntroState  # noqa: E402


def test_intro_manager_start_state() -> None:
    manager = IntroManager()
    manager.start()
    assert manager.state == IntroState.LOGO_IN


def test_intro_manager_transitions() -> None:
    config = IntroConfig(logo_in=0.1, weapons_in=0.1, hold=0.1, fade_out=0.1, allow_skip=False)
    manager = IntroManager(config=config)
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
    manager = IntroManager(config=config)
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
    manager = IntroManager(config=config)
    manager.start()

    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_s})
    manager.update(0.0, [event])

    assert manager.state == IntroState.LOGO_IN


def test_weapons_in_monotonic_then_hold_and_fade() -> None:
    config = IntroConfig(
        logo_in=0.0,
        weapons_in=1.0,
        hold=1.0,
        fade_out=1.0,
        allow_skip=False,
    )
    manager = IntroManager(config=config)
    manager.start()
    manager.update(0.0)

    state = manager.state
    assert state == IntroState.WEAPONS_IN

    previous = manager._progress()
    for _ in range(5):
        manager.update(0.2)
        progress = manager._progress()
        assert previous <= progress <= 1.0
        previous = progress

    state = manager.state
    assert state == IntroState.HOLD
    assert manager._progress() == pytest.approx(1.0)

    manager.update(0.5)
    state = manager.state
    assert state == IntroState.HOLD
    assert manager._progress() == pytest.approx(1.0)

    manager.update(0.5)
    state = manager.state
    assert state == IntroState.FADE_OUT
    fade_start = manager._progress()
    assert fade_start == pytest.approx(1.0)

    manager.update(0.5)
    fade_mid = manager._progress()
    assert 0.0 <= fade_mid < fade_start
    manager.update(0.25)
    assert manager._progress() < fade_mid
