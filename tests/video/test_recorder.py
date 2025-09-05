from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

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


def test_close_muxes_audio_successfully(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    recorder = Recorder(10, 10, 30, tmp_path / "out.mp4")
    recorder._video_path.write_bytes(b"frame")
    audio = DummyAudio(48_000)

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[bytes]:
        cmd = args[0]
        Path(cmd[-1]).write_bytes(b"muxed")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr("app.video.recorder.subprocess.run", fake_run)
    recorder.close(audio, rate=48_000)
    assert recorder.path.exists()
    assert not recorder._video_path.exists()
    assert not recorder.path.with_suffix(".wav").exists()


def test_close_raises_video_muxing_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    recorder = Recorder(10, 10, 30, tmp_path / "out.mp4")
    recorder._video_path.write_bytes(b"frame")
    audio = DummyAudio(48_000)
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
    assert not recorder.path.exists()
