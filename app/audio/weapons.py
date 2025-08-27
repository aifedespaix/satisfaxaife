from __future__ import annotations

"""High level helpers to play weapon related sounds."""

import threading
import time
from pathlib import Path
from typing import Literal, Optional

from .engine import AudioEngine


_DEFAULT_ENGINE: AudioEngine | None = None


def _get_default_engine() -> AudioEngine:
    """Return a shared :class:`AudioEngine` instance."""
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = AudioEngine()
    return _DEFAULT_ENGINE


class WeaponAudio:
    """Manage sounds for a single weapon."""

    def __init__(
        self,
        type: Literal["melee", "throw"],
        name: str,
        *,
        base_dir: str = "assets/weapons",
        engine: Optional[AudioEngine] = None,
        idle_gap: float = 1.0,
    ) -> None:
        self._type = type
        self._name = name
        self._engine = engine or _get_default_engine()
        self._idle_gap = idle_gap
        self._idle_thread: threading.Thread | None = None
        self._idle_running = threading.Event()

        base = Path(base_dir) / name
        self._idle_path: str | None
        self._touch_path: str | None
        self._throw_path: str | None
        if type == "melee":
            self._idle_path = str(base / "idle.ogg")
            self._touch_path = str(base / "touch.ogg")
            self._throw_path = None
        elif type == "throw":
            self._idle_path = None
            self._touch_path = str(base / "touch.ogg")
            self._throw_path = str(base / "throw.ogg")
        else:
            msg = f"Unknown weapon type: {type}"
            raise ValueError(msg)

    # ------------------------------------------------------------------
    # Melee idle management
    # ------------------------------------------------------------------
    def start_idle(self) -> None:
        """Start looping the idle sound for melee weapons."""
        if self._type != "melee" or self._idle_path is None:
            raise RuntimeError("Idle sound is only available for melee weapons")
        if self._idle_thread and self._idle_thread.is_alive():
            return
        self._idle_running.set()
        self._idle_thread = threading.Thread(target=self._idle_loop, daemon=True)
        self._idle_thread.start()

    def _idle_loop(self) -> None:
        assert self._idle_path is not None
        while self._idle_running.is_set():
            self._engine.play_variation(self._idle_path)
            length = self._engine.get_length(self._idle_path)
            time.sleep(length + self._idle_gap)

    def stop_idle(self) -> None:
        """Stop the idle loop for melee weapons."""
        if self._idle_thread and self._idle_thread.is_alive():
            self._idle_running.clear()
            self._idle_thread.join()
            self._idle_thread = None
            self._engine.stop_all()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def on_throw(self) -> None:
        """Play the throw sound for throwable weapons."""
        if self._throw_path is None:
            raise RuntimeError("This weapon type cannot throw")
        self._engine.play_variation(self._throw_path)

    def on_touch(self) -> None:
        """Play the touch/hit sound for any weapon."""
        if self._touch_path is None:
            raise RuntimeError("Touch sound not configured")
        self._engine.play_variation(self._touch_path)
