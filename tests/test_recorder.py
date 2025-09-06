from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pytest
from pytest import CaptureFixture, LogCaptureFixture

import imageio
from app.video.recorder import NullRecorder, Recorder


def test_recorder_preserves_dimensions(tmp_path: Path, capfd: CaptureFixture[str]) -> None:
    width, height = 100, 58
    recorder = Recorder(width, height, 30, tmp_path / "out.mp4")
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    recorder.add_frame(frame)
    recorder.close()
    err = capfd.readouterr().err
    assert "WARNING" not in err
    with imageio.get_reader(tmp_path / "out.mp4") as reader:
        out_frame = reader.get_data(0)
    assert out_frame.shape == (height, width, 3)


def test_null_recorder_path_is_none() -> None:
    """NullRecorder exposes a path attribute set to ``None``."""
    recorder = NullRecorder()
    assert recorder.path is None


def test_recorder_logs_each_second(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    width, height, fps = 10, 10, 5
    recorder = Recorder(width, height, fps, tmp_path / "out.mp4")
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    with caplog.at_level(logging.DEBUG, logger="app.video.recorder"):
        for _ in range(fps * 3):
            recorder.add_frame(frame)
    recorder.close()
    messages = [r.message for r in caplog.records if r.name == "app.video.recorder"]
    assert messages == [
        "Recorded 1 second(s) of video",
        "Recorded 2 second(s) of video",
        "Recorded 3 second(s) of video",
    ]


class DummyFormatError(RuntimeError):
    """Custom ``FormatError`` used for testing."""


@pytest.mark.parametrize("exc", [OSError, DummyFormatError])
def test_recorder_fallback_to_gif(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: LogCaptureFixture, exc: type[Exception]
) -> None:
    """Recorder falls back to GIF for expected errors."""

    original_get_writer = imageio.get_writer
    called = False

    def failing_once(*args: object, **kwargs: object) -> imageio._Writer:
        nonlocal called
        if not called:
            called = True
            raise exc("boom")
        return original_get_writer(*args, **kwargs)

    monkeypatch.setattr(imageio, "get_writer", failing_once)
    monkeypatch.setattr(imageio, "core", type("C", (), {"FormatError": DummyFormatError}))
    with caplog.at_level(logging.WARNING, logger="app.video.recorder"):
        recorder = Recorder(10, 10, 30, tmp_path / "out.mp4")
    assert recorder.path.suffix == ".gif"
    assert any(
        r.exc_info and "boom" in str(r.exc_info[1]) for r in caplog.records
    )


def test_recorder_unexpected_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Unexpected errors from ``imageio`` propagate."""

    def raise_value_error(*_args: object, **_kwargs: object) -> None:
        raise ValueError("fail")

    monkeypatch.setattr(imageio, "get_writer", raise_value_error)
    with pytest.raises(ValueError):
        Recorder(10, 10, 30, tmp_path / "out.mp4")
