"""Helpers to play ball-related sounds."""

from __future__ import annotations

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

    def __init__(self, *, base_dir: str = "assets/balls", engine: AudioEngine | None = None) -> None:
        self._engine = engine or get_default_engine()
        base = Path(base_dir)
        self._explode_path = str(base / "explose.ogg")

    def on_explode(self, timestamp: float | None = None) -> None:
        """Play the explosion sound when the ball is destroyed."""
        self._engine.play_variation(self._explode_path, timestamp=timestamp)
