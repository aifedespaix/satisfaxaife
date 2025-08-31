import os
from pathlib import Path
from typing import Any

import pytest

from app.audio import reset_default_engine
from app.core.config import settings
from app.core.types import Damage, EntityId
from app.game.match import create_controller
from app.render.renderer import Renderer
from app.weapons import weapon_registry
from app.weapons.base import Weapon, WorldView

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


class InstantKillWeapon(Weapon):  # type: ignore[misc]
    """Weapon that kills the opponent on the first update."""

    def __init__(self) -> None:
        super().__init__(name="instakill_test", cooldown=0.0, damage=Damage(200))
        self._done = False

    def update(self, owner: EntityId, view: WorldView, dt: float) -> None:
        if not self._done:
            enemy = view.get_enemy(owner)
            if enemy is not None:
                view.deal_damage(enemy, self.damage, timestamp=0.0)
                self._done = True
        super().update(owner, view, dt)


class DummyRecorder:
    """Recorder stub with a writable path attribute."""

    path: Path | None

    def __init__(self, path: Path) -> None:
        self.path = path

    def add_frame(self, _frame: Any) -> None:  # pragma: no cover - stub
        return None

    def close(self, audio: Any = None, rate: int = 48_000) -> None:  # pragma: no cover - stub
        return None


def test_append_slowmo_receives_death_timestamp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """append_slowmo_ending should get a timestamp including intro duration."""

    reset_default_engine()
    if "instakill_test" not in weapon_registry.names():
        weapon_registry.register("instakill_test", InstantKillWeapon)

    recorder = DummyRecorder(tmp_path / "out.mp4")
    renderer = Renderer(settings.width, settings.height)

    captured_path: Path | None = None
    captured_death: float | None = None

    def fake_append(
        path: Path,
        death_ts: float,
        pre_s: float,
        post_s: float,
        slow_factor: float,
        min_start: float = 0.0,
    ) -> None:
        nonlocal captured_path, captured_death
        captured_path = path
        captured_death = death_ts

    monkeypatch.setattr("app.game.controller.append_slowmo_ending", fake_append)

    controller = create_controller(
        "instakill_test", "instakill_test", recorder, renderer, max_seconds=1
    )
    controller.run()

    assert captured_death is not None
    assert controller.death_ts is not None
    assert captured_death == pytest.approx(controller.death_ts)
    intro_cfg = controller.intro_manager.config
    intro_duration = intro_cfg.logo_in + intro_cfg.weapons_in + intro_cfg.hold + intro_cfg.fade_out
    assert captured_death >= intro_duration

    weapon_registry._factories.pop("instakill_test")
    reset_default_engine()


def test_slowmo_segment_starts_after_intro(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Slow-motion extraction should never start before the intro ends."""

    reset_default_engine()
    if "instakill_test" not in weapon_registry.names():
        weapon_registry.register("instakill_test", InstantKillWeapon)

    recorder = DummyRecorder(tmp_path / "out.mp4")
    renderer = Renderer(settings.width, settings.height)

    captured_start: float | None = None
    captured_min: float | None = None

    def fake_append(
        path: Path,
        death_ts: float,
        pre_s: float,
        post_s: float,
        slow_factor: float,
        min_start: float = 0.0,
    ) -> None:
        nonlocal captured_start, captured_min
        captured_min = min_start
        captured_start = max(min_start, death_ts - pre_s)

    monkeypatch.setattr("app.game.controller.append_slowmo_ending", fake_append)

    controller = create_controller(
        "instakill_test", "instakill_test", recorder, renderer, max_seconds=1
    )
    controller.run()

    intro_cfg = controller.intro_manager.config
    intro_duration = intro_cfg.logo_in + intro_cfg.weapons_in + intro_cfg.hold + intro_cfg.fade_out

    assert captured_min is not None
    assert captured_start is not None
    assert captured_min == pytest.approx(intro_duration)
    assert captured_start == pytest.approx(intro_duration)

    weapon_registry._factories.pop("instakill_test")
    reset_default_engine()
