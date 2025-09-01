from __future__ import annotations

import logging
import subprocess
import wave
from pathlib import Path
from typing import Protocol

import imageio
import imageio_ffmpeg
import numpy as np

logger = logging.getLogger(__name__)


class RecorderProtocol(Protocol):
    """Minimal interface required from a video recorder.

    Any concrete implementation must provide a writable ``path`` attribute and
    implement :meth:`add_frame` and :meth:`close`. The ``path`` attribute may be
    ``None`` when the recorder does not persist any output (e.g. ``NullRecorder``).
    """

    path: Path | None

    def add_frame(self, frame: np.ndarray) -> None:
        """Append a pre-rendered frame to the output video."""

    def close(self, audio: np.ndarray | None = None, rate: int = 48_000) -> None:
        """Finalize the recording, optionally muxing an audio track."""


class Recorder(RecorderProtocol):
    """Write frames to a video file and optionally mux audio."""

    def __init__(self, width: int, height: int, fps: int, path: Path) -> None:
        self.width = width
        self.height = height
        self.fps = fps
        self.path = Path(path)
        self._format = "mp4"
        self._video_path = self.path.with_suffix(".video.mp4")
        self._frame_count = 0
        try:
            self.writer = imageio.get_writer(
                self._video_path,
                fps=fps,
                codec="libx264",
                macro_block_size=1,
            )
        except Exception:
            self._format = "gif"
            self._video_path = self.path.with_suffix(".gif")
            self.path = self._video_path
            self.writer = imageio.get_writer(self._video_path, fps=fps)

    def add_frame(self, frame: np.ndarray) -> None:
        """Append a pre-rendered frame to the output video."""
        self.writer.append_data(frame)
        self._frame_count += 1
        if self._frame_count % self.fps == 0:
            seconds = self._frame_count // self.fps
            logger.debug("Recorded %s second(s) of video", seconds)

    def close(self, audio: np.ndarray | None = None, rate: int = 48_000) -> None:
        """Finalize the video and optionally mux an audio track."""
        self.writer.close()
        if self._format != "mp4":
            return
        if audio is None or audio.size == 0:
            if self._video_path != self.path:
                self._video_path.rename(self.path)
            return
        audio_path = self.path.with_suffix(".wav")
        with wave.open(str(audio_path), "wb") as wf:
            channels = audio.shape[1] if audio.ndim == 2 else 1
            wf.setnchannels(channels)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            wf.writeframes(audio.tobytes())
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(self._video_path),
            "-i",
            str(audio_path),
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-shortest",
            str(self.path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        self._video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)


class NullRecorder(Recorder):
    """Recorder that discards frames and writes nothing.

    Attributes:
        path: Unused output path kept for API compatibility. Always ``None``.
    """

    path: Path | None  # type: ignore[assignment]

    def __init__(self) -> None:
        # ``Recorder`` expects an output path but ``NullRecorder`` never writes
        # anything. ``path`` is therefore set to ``None`` and should not be
        # relied upon by callers.
        self.path = None

    def add_frame(self, _frame: np.ndarray) -> None:  # noqa: D401 - same interface
        """Ignore a pre-rendered frame."""

    def close(self, _audio: np.ndarray | None = None, rate: int = 48_000) -> None:  # noqa: D401 - same interface
        """No-op close method."""
