from __future__ import annotations

import logging
import subprocess
import wave
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from app.video.recorder import Recorder, VideoMuxingError


class DummyAudio:
    """Minimal array-like object representing PCM audio samples."""

    def __init__(self, samples: int, channels: int = 1) -> None:
        self.ndim = 2 if channels > 1 else 1
        self.shape = (samples, channels) if channels > 1 else (samples,)
        self.size = samples * channels
        self._data = b"\x00" * self.size * 2

    def tobytes(self) -> bytes:
        return self._data


def test_close_muxes_audio_successfully(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = Recorder(10, 10, 30, tmp_path / "out.mp4")
    recorder._video_path.write_bytes(b"frame")
    recorder._frame_count = 1
    audio = DummyAudio(48_000)

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        cmd = args[0]
        Path(cmd[-1]).write_bytes(b"muxed")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("app.video.recorder.subprocess.run", fake_run)
    recorder.close(audio, rate=48_000)
    assert recorder.path is not None
    path = recorder.path
    assert path.exists()
    assert not recorder._video_path.exists()
    assert not path.with_suffix(".wav").exists()


def test_close_converts_float_audio(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = Recorder(10, 10, 30, tmp_path / "out.mp4")
    recorder._video_path.write_bytes(b"frame")
    recorder._frame_count = 1
    audio = np.array([0.0, 0.5, -1.0], dtype=np.float32)
    expected = (
        np.clip(audio, -1.0, 1.0) * np.iinfo(np.int16).max
    ).astype(np.int16).tobytes()

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        cmd = args[0]
        audio_file = Path(cmd[5])
        with wave.open(str(audio_file), "rb") as wf:
            frames = wf.readframes(wf.getnframes())
        assert frames == expected
        Path(cmd[-1]).write_bytes(b"muxed")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("app.video.recorder.subprocess.run", fake_run)
    recorder.close(audio, rate=48_000)
    assert recorder.path is not None
    path = recorder.path
    assert path.exists()
    assert not recorder._video_path.exists()
    assert not path.with_suffix(".wav").exists()


def test_close_raises_video_muxing_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    recorder = Recorder(10, 10, 30, tmp_path / "out.mp4")
    recorder._video_path.write_bytes(b"frame")
    recorder._frame_count = 1
    audio = DummyAudio(48_000)
    assert recorder.path is not None
    audio_path = recorder.path.with_suffix(".wav")

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        raise subprocess.CalledProcessError(1, args[0], stderr="boom")

    monkeypatch.setattr("app.video.recorder.subprocess.run", fake_run)
    with caplog.at_level(logging.ERROR, logger="app.video.recorder"):
        with pytest.raises(VideoMuxingError) as excinfo:
            recorder.close(audio, rate=48_000)
    assert "boom" in str(excinfo.value)
    assert "boom" in caplog.text
    assert not recorder._video_path.exists()
    assert not audio_path.exists()
    assert recorder.path is not None
    assert not recorder.path.exists()


def test_close_without_frames_does_not_raise(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Closing without frames logs a warning and sets ``path`` to ``None``."""
    recorder = Recorder(10, 10, 30, tmp_path / "out.mp4")
    audio = DummyAudio(48_000)
    with caplog.at_level(logging.WARNING, logger="app.video.recorder"):
        recorder.close(audio, rate=48_000)
    assert "No video frames recorded; skipping muxing" in caplog.text
    assert recorder.path is None
    assert not recorder._video_path.exists()
