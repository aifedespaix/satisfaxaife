from __future__ import annotations

import logging
import subprocess
import wave
from pathlib import Path
from typing import Protocol

import numpy as np

import imageio
import imageio_ffmpeg

logger = logging.getLogger(__name__)


def _ensure_int16(audio: np.ndarray) -> np.ndarray:
    """Return ``audio`` as 16-bit PCM samples.

    Floating point arrays are clipped to ``[-1.0, 1.0]`` and scaled to the
    signed 16-bit range. Integer arrays are cast without scaling.
    """

    if audio.dtype == np.int16:
        return audio
    if np.issubdtype(audio.dtype, np.floating):
        scaled = np.clip(audio, -1.0, 1.0) * np.iinfo(np.int16).max
        return scaled.astype(np.int16)
    return audio.astype(np.int16, copy=False)


class VideoMuxingError(RuntimeError):
    """Raised when combining video and audio streams fails."""


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

    path: Path | None

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
        except (OSError, imageio.core.FormatError) as exc:
            logger.warning("MP4 writer unavailable, falling back to GIF", exc_info=exc)
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
        """Finalize the video and optionally mux an audio track.

        The method returns early if no frames were recorded or if the temporary
        video file is missing. In that case a warning is logged and any provided
        audio is ignored. Audio samples must use the ``np.int16`` dtype; other
        dtypes are converted with clipping and scaling.

        Parameters
        ----------
        audio:
            PCM samples in ``np.int16`` format. Floating point arrays in the
            ``[-1.0, 1.0]`` range are scaled and converted to ``np.int16``.
        rate:
            Sampling rate of ``audio`` in Hertz.

        Raises
        ------
        VideoMuxingError
            If ``ffmpeg`` fails to combine audio and video streams.
        """
        self.writer.close()
        if self._frame_count == 0 or not self._video_path.exists():
            logger.warning("No video frames recorded; skipping muxing")
            self.path = None
            return
        assert self.path is not None
        if self._format != "mp4":
            return
        if audio is None or audio.size == 0:
            if self._video_path != self.path:
                self._video_path.rename(self.path)
            return
        audio = _ensure_int16(audio)
        assert audio.dtype == np.int16
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
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            logger.error("ffmpeg muxing failed: %s", exc.stderr)
            self._video_path.unlink(missing_ok=True)
            audio_path.unlink(missing_ok=True)
            raise VideoMuxingError(exc.stderr) from exc
        self._video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)


class NullRecorder(Recorder):
    """Recorder that discards frames and writes nothing.

    Attributes:
        path: Unused output path kept for API compatibility. Always ``None``.
    """

    path: Path | None

    def __init__(self) -> None:
        # ``Recorder`` expects an output path but ``NullRecorder`` never writes
        # anything. ``path`` is therefore set to ``None`` and should not be
        # relied upon by callers.
        self.path = None

    def add_frame(self, _frame: np.ndarray) -> None:  # noqa: D401 - same interface
        """Ignore a pre-rendered frame."""

    def close(self, _audio: np.ndarray | None = None, rate: int = 48_000) -> None:  # noqa: D401 - same interface
        """No-op close method."""
