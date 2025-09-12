"""Helpers to play ball-related sounds."""

from __future__ import annotations

import random
from pathlib import Path

from .engine import AudioEngine
from .weapons import get_default_engine


class BallAudio:
    """Manage sounds for a single ball entity.

    Parameters
    ----------
    base_dir:
        Directory containing ball sound assets. Defaults to ``assets/balls``.
    engine:
        Optional :class:`AudioEngine` to use. If omitted, the shared default
        engine is used.
    """

    def __init__(
        self, *, base_dir: str = "assets/balls", engine: AudioEngine | None = None
    ) -> None:
        self._engine = engine or get_default_engine()
        base = Path(base_dir)
        self._explode_path = str(base / "explose.ogg")
        self._hit_paths: list[str] = [
            str(base / "hit-a.ogg"),
            str(base / "hit-b.ogg"),
            str(base / "hit-c.ogg"),
        ]

    def on_explode(self, timestamp: float | None = None) -> None:
        """Play the explosion sound when the ball is destroyed."""
        self._engine.play_variation(self._explode_path, timestamp=timestamp)

    def on_hit(self, timestamp: float | None = None) -> None:
        """Play a random hit sound when the ball takes damage."""
        self._engine.play_variation(random.choice(self._hit_paths), timestamp=timestamp)

    def on_bump(self, *, volume: float, timestamp: float | None = None, cooldown_ms: int | None = None) -> None:
        """Play a soft, attenuated hit sound for non-damaging bumps.

        Parameters
        ----------
        volume:
            Linear volume [0.0, 1.0] applied to the variation.
        timestamp:
            Optional simulated time used during recording capture.
        cooldown_ms:
            Optional cooldown in milliseconds to limit repetition.
        """
        path = random.choice(self._hit_paths)
        self._engine.play_variation(path, volume=volume, timestamp=timestamp, cooldown_ms=cooldown_ms)
