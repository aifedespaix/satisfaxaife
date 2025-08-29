"""High level helpers to play weapon related sounds."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Literal

import pygame

from .engine import AudioEngine

_DEFAULT_ENGINE: AudioEngine | None = None


def get_default_engine() -> AudioEngine:
    """Return a shared :class:`AudioEngine` instance."""
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = AudioEngine()
    return _DEFAULT_ENGINE


def reset_default_engine() -> None:
    """Shutdown and clear the shared :class:`AudioEngine`."""
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is not None:
        _DEFAULT_ENGINE.shutdown()
        _DEFAULT_ENGINE = None


class WeaponAudio:
    """Manage sounds for a single weapon."""

    def __init__(
        self,
        type: Literal["melee", "throw"],
        name: str,
        *,
        base_dir: str = "assets/weapons",
        engine: AudioEngine | None = None,
        idle_gap: float = 1.0,
    ) -> None:
        self._type = type
        self._name = name
        self._engine = engine or get_default_engine()
        self._idle_gap = idle_gap
        self._idle_thread: threading.Thread | None = None
        self._idle_running = threading.Event()
        self._idle_handle: pygame.mixer.Channel | None = None
        self._idle_lock = threading.Lock()

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
    def start_idle(self, timestamp: float | None = None) -> None:
        """Start looping the idle sound for melee weapons."""
        if self._type != "melee" or self._idle_path is None:
            raise RuntimeError("Idle sound is only available for melee weapons")
        if self._idle_thread and self._idle_thread.is_alive():
            return
        self._idle_running.set()
        self._idle_thread = threading.Thread(target=self._idle_loop, args=(timestamp,), daemon=True)
        self._idle_thread.start()

    def _idle_loop(self, timestamp: float | None) -> None:
        assert self._idle_path is not None
        current = timestamp
        while self._idle_running.is_set():
            handle = self._engine.play_variation(self._idle_path, timestamp=current)
            if handle is not None:
                with self._idle_lock:
                    self._idle_handle = handle
            length = self._engine.get_length(self._idle_path)
            if current is not None:
                current += length + self._idle_gap
            time.sleep(length + self._idle_gap)

    def stop_idle(self, timestamp: float | None = None) -> None:
        """Stop the idle loop for melee weapons.

        The idle sound is stopped using :meth:`AudioEngine.stop_handle` so
        that other effects (for example the explosion triggered on death)
        keep playing.  Passing ``timestamp`` trims the captured idle audio at
        the provided time.

        Parameters
        ----------
        timestamp:
            Optional capture time in seconds used to truncate the recorded
            idle sound.
        """
        if self._idle_thread and self._idle_thread.is_alive():
            self._idle_running.clear()
            with self._idle_lock:
                handle = self._idle_handle
                self._idle_handle = None
            if handle is not None:
                self._engine.stop_handle(handle, timestamp)
            self._idle_thread.join()
            self._idle_thread = None

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def on_throw(self, timestamp: float | None = None) -> None:
        """Play the throw sound for throwable weapons."""
        if self._throw_path is None:
            raise RuntimeError("This weapon type cannot throw")
        self._engine.play_variation(self._throw_path, timestamp=timestamp)

    def on_touch(self, timestamp: float | None = None) -> None:
        """Play the touch/hit sound for any weapon."""
        if self._touch_path is None:
            raise RuntimeError("Touch sound not configured")
        self._engine.play_variation(self._touch_path, timestamp=timestamp)
