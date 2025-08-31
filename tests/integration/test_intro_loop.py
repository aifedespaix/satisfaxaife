from __future__ import annotations

from app.core.config import settings
from app.game.controller import GameController
from app.game.intro import IntroManager
from app.game.match import create_controller
from app.render.hud import Hud
from app.render.renderer import Renderer
from tests.integration.helpers import SpyRecorder


class StubIntroManager(IntroManager):
    """Intro manager stub used to control flow during tests."""

    def __init__(self, frames: int, skip_at: int | None = None) -> None:
        super().__init__(labels=("", ""))
        self.frames = frames
        self.skip_at = skip_at
        self.updates = 0
        self.draws = 0

    def is_finished(self) -> bool:  # pragma: no cover - simple predicate
        return self._skipped or self.updates >= self.frames

    def update(self, dt: float) -> None:  # pragma: no cover - simple counter
        self.updates += 1
        if self.skip_at is not None and self.updates >= self.skip_at:
            self.skip()

    def draw(self, renderer: Renderer, hud: Hud) -> None:  # pragma: no cover - simple counter
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
