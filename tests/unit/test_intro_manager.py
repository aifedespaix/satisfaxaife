from __future__ import annotations

import pygame

from app.intro import IntroConfig, IntroManager, IntroState


def test_intro_manager_start_state() -> None:
    manager = IntroManager()
    manager.start()
    assert manager.state == IntroState.LOGO_IN


def test_intro_manager_transitions() -> None:
    config = IntroConfig(logo_in=0.1, weapons_in=0.1, hold=0.1, fade_out=0.1)
    manager = IntroManager(config=config, allow_skip=False)
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
    config = IntroConfig(logo_in=10.0, weapons_in=10.0, hold=10.0, fade_out=10.0)
    manager = IntroManager(config=config, allow_skip=True, skip_key=pygame.K_s)
    manager.start()

    event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_s})
    manager.update(0.0, [event])

    assert manager.state == IntroState.DONE
    assert manager.is_finished()
