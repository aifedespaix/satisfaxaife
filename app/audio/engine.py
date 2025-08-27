from __future__ import annotations

"""Low-level audio engine based on :mod:`pygame.mixer`.

The engine loads sounds, precomputes six pitch variations using linear
resampling and caches them in memory. Each playback selects a variation at
random and applies a short fade-in to avoid clicks. A cooldown prevents the
same sound from being triggered too frequently.
"""

from pathlib import Path
import random
import threading
import time
from typing import Dict, List

import numpy as np
import pygame
import pygame.sndarray


class AudioEngine:
    """Play sounds with pitch variations and spam protection."""

    SAMPLE_RATE: int = 48_000
    CHANNELS: int = 2
    BUFFER: int = 1024
    DEFAULT_VOLUME: float = 0.8
    COOLDOWN_MS: int = 80
    FADE_MS: int = 5
    PITCH_FACTORS: List[float] = [2 ** (s / 12) for s in (-3, -2, -1, 0, 1, 2)]

    def __init__(self) -> None:
        pygame.mixer.init(
            frequency=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            buffer=self.BUFFER,
        )
        self._cache: Dict[str, List[pygame.mixer.Sound]] = {}
        self._lengths: Dict[str, float] = {}
        self._last_play: Dict[str, float] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def shutdown(self) -> None:
        """Stop all sounds and quit the mixer."""
        pygame.mixer.stop()
        pygame.mixer.quit()

    def stop_all(self) -> None:
        """Fade out all playing sounds."""
        pygame.mixer.fadeout(self.FADE_MS)

    def get_length(self, path: str) -> float:
        """Return the length in seconds of ``path``."""
        self._ensure_variations(path)
        return self._lengths[path]

    def play_variation(self, path: str, volume: float | None = None) -> bool:
        """Play ``path`` with a random pitch variation.

        Parameters
        ----------
        path:
            Path to the sound file.
        volume:
            Optional volume between 0 and 1. Defaults to ``DEFAULT_VOLUME``.

        Returns
        -------
        bool
            ``True`` if the sound was played, ``False`` if skipped due to
            cooldown.
        """
        now = time.perf_counter()
        with self._lock:
            last = self._last_play.get(path)
            if last is not None and (now - last) * 1000 < self.COOLDOWN_MS:
                return False
            sounds = self._ensure_variations(path)
            sound = random.choice(sounds)
            sound.set_volume(volume if volume is not None else self.DEFAULT_VOLUME)
            sound.play(fade_ms=self.FADE_MS)
            self._last_play[path] = now
            return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_variations(self, path: str) -> List[pygame.mixer.Sound]:
        if path not in self._cache:
            if not Path(path).is_file():
                msg = f"Sound file not found: {path}"
                raise FileNotFoundError(msg)
            original = pygame.mixer.Sound(path)
            array = pygame.sndarray.array(original)
            self._lengths[path] = original.get_length()
            variations: List[pygame.mixer.Sound] = []
            for factor in self.PITCH_FACTORS:
                resampled = self._resample(array, factor)
                sound = pygame.sndarray.make_sound(resampled)
                variations.append(sound)
            self._cache[path] = variations
        return self._cache[path]

    @staticmethod
    def _resample(array: np.ndarray, factor: float) -> np.ndarray:
        """Resample ``array`` by ``factor`` using linear interpolation."""
        original = array.astype(np.float32)
        if original.ndim == 1:
            length = original.shape[0]
            new_length = int(length / factor)
            indices = np.arange(new_length) * factor
            resampled = np.interp(indices, np.arange(length), original)
            resampled = np.clip(resampled, -32768, 32767).astype(np.int16)
            return resampled
        length = original.shape[0]
        new_length = int(length / factor)
        indices = np.arange(new_length) * factor
        resampled = np.empty((new_length, original.shape[1]), dtype=np.float32)
        for channel in range(original.shape[1]):
            resampled[:, channel] = np.interp(
                indices, np.arange(length), original[:, channel]
            )
        resampled = np.clip(resampled, -32768, 32767).astype(np.int16)
        return resampled
