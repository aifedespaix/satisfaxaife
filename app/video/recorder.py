from __future__ import annotations

from pathlib import Path

import imageio
import numpy as np

from app.core.config import settings
from app.core.types import Color

_DIGITS = {
    "0": ("111", "101", "101", "101", "111"),
    "1": ("010", "110", "010", "010", "111"),
    "2": ("111", "001", "111", "100", "111"),
    "3": ("111", "001", "111", "001", "111"),
    "4": ("101", "101", "111", "001", "001"),
    "5": ("111", "100", "111", "001", "111"),
    "6": ("111", "100", "111", "101", "111"),
    "7": ("111", "001", "010", "010", "010"),
    "8": ("111", "101", "111", "101", "111"),
    "9": ("111", "101", "111", "001", "111"),
}


class Recorder:
    """Write frames to an MP4 file with GIF fallback."""

    def __init__(self, width: int, height: int, fps: int, path: Path) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.path = Path(path)
        try:
            self.writer = imageio.get_writer(self.path, fps=fps, codec="libx264")
        except Exception:
            self.path = self.path.with_suffix(".gif")
            self.writer = imageio.get_writer(self.path, fps=fps)

    def _draw_number(self, frame: np.ndarray, number: int, color: Color) -> None:
        scale = 8
        x = 10
        y = 10
        for char in str(number):
            pattern = _DIGITS[char]
            for row, line in enumerate(pattern):
                for col, bit in enumerate(line):
                    if bit == "1":
                        x0 = x + col * scale
                        y0 = y + row * scale
                        frame[y0 : y0 + scale, x0 : x0 + scale] = color
            x += (len(pattern[0]) + 1) * scale

    def add_frame(self, frame_number: int) -> None:
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:, :] = np.array(settings.background_color, dtype=np.uint8)
        self._draw_number(frame, frame_number, (255, 255, 255))
        self.writer.append_data(frame)

    def close(self) -> None:
        self.writer.close()
