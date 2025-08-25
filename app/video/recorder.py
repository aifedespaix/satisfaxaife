from __future__ import annotations

from pathlib import Path

import imageio
import numpy as np


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

    def add_frame(self, frame: np.ndarray) -> None:
        """Append a pre-rendered frame to the output video."""
        self.writer.append_data(frame)

    def close(self) -> None:
        """Finalize and close the video file."""
        self.writer.close()
