from __future__ import annotations

import subprocess
from pathlib import Path

from app.core.config import settings
from app.core.types import Damage, EntityId, Vec2
from app.game.intro import IntroManager
from app.game.match import run_match
from app.render.renderer import Renderer
from app.video.recorder import Recorder
from app.weapons import weapon_registry
from app.weapons.base import Weapon, WorldView

EVENT_TIME = 2.0


class DelayedKillWeapon(Weapon):
    """Weapon that kills the opponent at a fixed timestamp."""

    def __init__(self) -> None:
        super().__init__(name="instakill", cooldown=0.0, damage=Damage(200))
        self._done = False
        self._elapsed = 0.0

    def _fire(
        self, owner: EntityId, view: WorldView, direction: Vec2
    ) -> None:  # pragma: no cover - stub
        return None

    def update(self, owner: EntityId, view: WorldView, dt: float) -> None:
        if not self._done:
            self._elapsed += dt
            if self._elapsed >= EVENT_TIME:
                enemy = view.get_enemy(owner)
                if enemy is not None:
                    view.deal_damage(enemy, self.damage, timestamp=EVENT_TIME)
                    self._done = True
        super().update(owner, view, dt)


def _stream_duration(path: Path, stream: str) -> float:
    ffprobe = "ffprobe"
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-select_streams",
            f"{stream}:0",
            "-show_entries",
            "stream=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def test_postprocessed_slowmo(tmp_path: Path) -> None:
    if "instakill" not in weapon_registry.names():
        weapon_registry.register("instakill", DelayedKillWeapon)
    out = tmp_path / "slowmo.mp4"
    recorder = Recorder(settings.width, settings.height, settings.fps, out)
    renderer = Renderer(settings.width, settings.height)
    run_match("instakill", "instakill", recorder, renderer, max_seconds=5)
    assert out.exists()
    video_dur = _stream_duration(out, "v")
    audio_dur = _stream_duration(out, "a")
    assert abs(video_dur - audio_dur) < 0.1
    intro_duration = IntroManager()._duration
    expected = (
        intro_duration
        + EVENT_TIME
        + settings.end_screen.explosion_duration
        + (settings.end_screen.pre_s + settings.end_screen.post_s) / settings.end_screen.slow_factor
    )
    assert expected - 0.1 < video_dur < expected + 0.1
