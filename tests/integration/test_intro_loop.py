from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import pytest

pytest.importorskip("pydantic")

from app.core.config import settings
from app.game.controller import GameController
from app.game.match import create_controller
from app.intro import IntroConfig, IntroManager, IntroState
from app.render.renderer import Renderer
from tests.integration.helpers import SpyRecorder

if TYPE_CHECKING:  # pragma: no cover - typing only
    import pygame
else:  # pragma: no cover - skip if missing at runtime
    pygame = pytest.importorskip("pygame")


class StubIntroManager(IntroManager):
    """Intro manager stub used to control flow during tests."""

    def __init__(self, frames: int, skip_at: int | None = None) -> None:
        super().__init__(config=IntroConfig(logo_in=0.0, weapons_in=0.0, hold=0.0, fade_out=0.0))
        self.frames = frames
        self.skip_at = skip_at
        self.updates = 0
        self.draws = 0
        self._skipped = False

    def start(self) -> None:  # pragma: no cover - override
        return

    def is_finished(self) -> bool:  # pragma: no cover - simple predicate
        return self._skipped or self.updates >= self.frames

    def update(
        self, dt: float, events: Sequence[pygame.event.Event] | None = None
    ) -> None:  # pragma: no cover - simple counter
        self.updates += 1
        if self.skip_at is not None and self.updates >= self.skip_at:
            self._skipped = True

    def draw(
        self, surface: pygame.Surface, labels: tuple[str, str]
    ) -> None:  # pragma: no cover - simple counter
        self.draws += 1


def _make_controller(intro: StubIntroManager) -> GameController:
    recorder = SpyRecorder()
    renderer = Renderer(settings.width, settings.height)
    controller = create_controller("katana", "shuriken", recorder, renderer, max_seconds=0)
    controller.intro_manager = intro
    return controller


def test_intro_runs_to_completion() -> None:
    intro = StubIntroManager(frames=3)
    controller = _make_controller(intro)
    controller.run()
    assert intro.updates == 3 and intro.draws == 3
    assert controller.elapsed == 0.0


def test_intro_can_be_skipped() -> None:
    intro = StubIntroManager(frames=5, skip_at=1)
    controller = _make_controller(intro)
    controller.run()
    assert intro.updates == 1 and intro.draws == 1
    assert controller.elapsed == 0.0


def test_intro_durations() -> None:
    """Intro holds for 1s then fades out over 0.25s."""
    config = IntroConfig(
        logo_in=0.0,
        weapons_in=0.0,
        hold=1.0,
        fade_out=0.25,
        allow_skip=False,
    )
    intro = IntroManager(config=config)
    intro.start()
    intro.update(0.0)
    intro.update(0.0)
    assert intro.state is IntroState.HOLD

    held: float = 0.0
    while intro.state is IntroState.HOLD:
        intro.update(0.1)
        held += 0.1
    assert intro.state is IntroState.FADE_OUT
    assert held == pytest.approx(1.0)

    faded: float = 0.0
    while intro.state is IntroState.FADE_OUT:
        intro.update(0.05)
        faded += 0.05
    assert intro.is_finished()
    assert faded == pytest.approx(0.25)
