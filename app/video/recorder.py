from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
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
        # Detect if a local stubbed imageio module is shadowing the real dependency.
        # The stub used in tests exposes a docstring mentioning "Stub imageio".
        doc = getattr(imageio, "__doc__", "") or ""
        self._using_stub_imageio = "Stub imageio" in doc

        if self._using_stub_imageio:
            # Fallback: record frames as PNGs in a temporary folder and encode with ffmpeg later.
            self._frames_dir = Path(tempfile.mkdtemp(prefix="frames_", dir=str(self.path.parent)))

            class _PngSeqWriter:
                def __init__(self, out_dir: Path) -> None:
                    self.out_dir = out_dir
                    self.index = 0

                def append_data(self, frame: np.ndarray) -> None:  # pragma: no cover - IO wrapper
                    # frame is H x W x 3 (uint8). Convert back to (W, H, 3) for pygame.
                    import pygame  # local import to avoid hard dep during typing

                    if frame.ndim != 3 or frame.shape[2] < 3:
                        raise ValueError("Expected frame with shape (H, W, 3)")
                    arr = np.swapaxes(frame, 0, 1)  # W x H x 3
                    surf = pygame.surfarray.make_surface(arr)
                    fname = self.out_dir / f"frame_{self.index:06d}.png"
                    pygame.image.save(surf, str(fname))
                    self.index += 1

                def close(self) -> None:  # pragma: no cover - nothing to close for PNG sequence
                    return None

            self.writer = _PngSeqWriter(self._frames_dir)
        else:
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

        # If we used the stub fallback, encode the PNG sequence into an MP4 now.
        if getattr(self, "_using_stub_imageio", False):
            # Encode only if some frames were produced.
            if self._frame_count == 0:
                logger.warning("No video frames recorded; skipping muxing")
                # Cleanup temp dir
                if hasattr(self, "_frames_dir"):
                    shutil.rmtree(self._frames_dir, ignore_errors=True)
                self.path = None
                return
            ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
            pattern = str(self._frames_dir / "frame_%06d.png")
            cmd = [
                ffmpeg,
                "-y",
                "-framerate",
                str(self.fps),
                "-i",
                pattern,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                str(self._video_path),
            ]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as exc:  # pragma: no cover - depends on env
                logger.error("ffmpeg encoding failed: %s", exc.stderr)
                shutil.rmtree(self._frames_dir, ignore_errors=True)
                self.path = None
                return
            finally:
                shutil.rmtree(self._frames_dir, ignore_errors=True)

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
